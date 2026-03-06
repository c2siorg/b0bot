from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Optional

from sentence_transformers import SentenceTransformer

from dotenv import load_dotenv
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app_config import Settings
from exceptions import LLMNotFoundError, LLMProcessingError, NewsFetchError
from repositories.news_repository import NewsRepository
from schemas.news import NewsItem, NewsResponse

load_dotenv()

logger = logging.getLogger(__name__)


class NewsService:
    def __init__(self, repository: NewsRepository, settings: Settings) -> None:
        self._repository = repository
        self._settings = settings
        self._llm_config: dict[str, str] = self._load_llm_config()
        self._news_format = "[title, source, date(DD/MM/YYYY), news url];"
        self._embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        logger.info("Loaded embedding model 'all-MiniLM-L6-v2'")

        self._chat_models: dict[str, ChatHuggingFace] = {}
        for model_name, repo_id in self._llm_config.items():
            try:
                llm = HuggingFaceEndpoint(
                    repo_id=repo_id,
                    temperature=self._settings.llm_temperature,
                    max_new_tokens=1024,
                    huggingfacehub_api_token=settings.huggingfacehub_api_token,
                )
                self._chat_models[model_name] = ChatHuggingFace(llm=llm)
                logger.info("Initialised ChatHuggingFace for '%s' (%s)", model_name, repo_id)
            except Exception as exc:
                logger.warning(
                    "Could not initialise model '%s' (%s): %s",
                    model_name,
                    repo_id,
                    exc,
                )

    def _load_llm_config(self) -> dict[str, str]:
        with open(self._settings.llm_config_path, "r", encoding="utf-8") as fh:
            return json.load(fh)

    @property
    def available_models(self) -> list[str]:
        return list(self._llm_config.keys())


    def _get_chat_model(self, model_name: str) -> ChatHuggingFace:
        chat_model = self._chat_models.get(model_name)
        if chat_model is None:
            raise LLMNotFoundError(model_name, available=self.available_models)
        return chat_model


    @staticmethod
    def _load_prompt_messages(path: str) -> list[dict]:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)

    def _build_messages(
        self,
        news_data: list[dict],
        user_keywords: Optional[str] = None,
    ) -> list:
        """
        Load the prompt template, fill placeholders, and convert
        to langchain message objects (SystemMessage / HumanMessage / AIMessage).
        """
        template_path = (
            "prompts/withkey.json" if user_keywords else "prompts/withoutkey.json"
        )
        raw_messages = self._load_prompt_messages(template_path)

        langchain_messages = []

        for msg in raw_messages:
            content: str = msg["content"]
            content = content.replace("<news_data_placeholder>", str(news_data))
            if user_keywords:
                content = content.replace("<user_keywords_placeholder>", user_keywords)
            content = content.replace("{news_format}", self._news_format)
            content = content.replace(
                "{news_number}", str(self._settings.max_news_results)
            )

            role = msg["role"]
            if role == "system":
                langchain_messages.append(SystemMessage(content=content))
            elif role == "user":
                langchain_messages.append(HumanMessage(content=content))
            elif role == "assistant":
                langchain_messages.append(AIMessage(content=content))

        return langchain_messages


    def _invoke_llm_sync(
        self,
        chat_model: ChatHuggingFace,
        messages: list,
    ) -> str:
        """
        Call the HuggingFace Serverless Inference API via ChatHuggingFace.
        Returns the text content of the model response.
        """
        response = chat_model.invoke(messages)
        content = response.content
        logger.info("--- RAW LLM RESPONSE START ---")
        logger.info(content)
        logger.info("--- RAW LLM RESPONSE END ---")
        return content

    def _parse_llm_output(self, raw_output: str) -> list[NewsItem]:
        if not raw_output or not raw_output.strip():
            return []

        import re
        processed_output = re.sub(r"<think>.*?</think>", "", raw_output, flags=re.DOTALL).strip()

        news_items: list[NewsItem] = []

        for line in processed_output.splitlines():
            line = line.strip()
            if not line:
                continue
            
            line = re.sub(r"^[`\s\*\-\d\.]+", "", line) 
            
            if "[" not in line:
                continue

            start_idx = line.find("[")
            end_idx = line.rfind("]")
            
            if start_idx == -1 or end_idx == -1 or end_idx <= start_idx:
                continue
                
            cleaned = line[start_idx + 1 : end_idx].strip()
            if not cleaned:
                continue

            parts = [p.strip().strip("\"'") for p in cleaned.split(",", maxsplit=3)]

            if len(parts) < 2:
                continue

            try:
                item = NewsItem(
                    title=parts[0] if len(parts) > 0 else "No title provided",
                    source=parts[1] if len(parts) > 1 else "No source provided",
                    date=parts[2] if len(parts) > 2 else "No date provided",
                    url=parts[3].strip() if len(parts) > 3 else "No URL provided",
                )
                news_items.append(item)
            except Exception as exc:
                logger.warning("Skipping unparseable line %r - %s", line, exc)

        return news_items


    async def get_news(
        self,
        llm_name: str,
        keywords: Optional[str] = None,
    ) -> NewsResponse:

        _ = self._get_chat_model(llm_name)

        try:
            if keywords:
                # Embed keywords and do vector similarity search
                vector = self._embedding_model.encode(keywords).tolist()
                news_data: list[dict] = await asyncio.to_thread(
                    self._repository.search_by_vector,
                    vector,
                    self._settings.max_news_results,
                )
            else:
                # No keywords — fetch all news
                news_data = await asyncio.to_thread(
                    self._repository.get_news_collections
                )
                news_data = news_data[: self._settings.max_news_results]
        except Exception as exc:
            logger.error("Pinecone fetch failed: %s", exc)
            raise NewsFetchError(f"Knowledge-base query failed: {exc}") from exc

        if not news_data:
            logger.warning("No news found in Pinecone namespace.")
            return NewsResponse(llm=llm_name, keywords=keywords, count=0, news=[])

        news_items: list[NewsItem] = []

        for item in news_data:
            news_items.append(
                NewsItem(
                    title=item.get("headlines", "No title provided"),
                    source=item.get("author", "Unknown source"),
                    date=item.get("newsDate", "Unknown date"),
                    url=item.get("newsURL", "No URL provided"),
                )
            )

        logger.info("Returning %d news items.", len(news_items))

        return NewsResponse(
            llm=llm_name,
            keywords=keywords,
            count=len(news_items),
            news=news_items,
        )