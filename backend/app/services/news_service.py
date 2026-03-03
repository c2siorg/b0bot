from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Optional

from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_community.llms import HuggingFaceEndpoint

from app.config import Settings
from app.exceptions import LLMNotFoundError, LLMProcessingError, NewsFetchError
from app.repositories.news_repository import NewsRepository
from app.schemas.news import NewsItem, NewsResponse

logger = logging.getLogger(__name__)


class NewsService:
    def __init__(self, repository: NewsRepository, settings: Settings) -> None:
        self._repository = repository
        self._settings = settings
        self._llm_cache: dict[str, HuggingFaceEndpoint] = {}
        self._llm_config: dict[str, str] = self._load_llm_config()
        self._news_format = "[title, source, date(DD/MM/YYYY), news url];"

        os.environ["HUGGINGFACEHUB_API_TOKEN"] = settings.huggingface_token

    def _load_llm_config(self) -> dict[str, str]:
        """Load ``{ short_name: huggingface_repo_id }`` from the JSON file."""
        with open(self._settings.llm_config_path, "r", encoding="utf-8") as fh:
            return json.load(fh)

    @property
    def available_models(self) -> list[str]:
        return list(self._llm_config.keys())

    def _get_llm(self, model_name: str) -> HuggingFaceEndpoint:
        if model_name in self._llm_cache:
            return self._llm_cache[model_name]

        repo_id = self._llm_config.get(model_name)
        if not repo_id:
            raise LLMNotFoundError(model_name, available=self.available_models)

        llm = HuggingFaceEndpoint(
            repo_id=repo_id,
            temperature=self._settings.llm_temperature,
            token=self._settings.huggingface_token,
        )
        self._llm_cache[model_name] = llm
        return llm

    @staticmethod
    def _load_prompt_messages(path: str) -> list[dict]:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)

    def _build_messages(
        self,
        news_data: list[dict],
        user_keywords: Optional[str] = None,
    ) -> list[dict]:
        
        template_path = (
            "prompts/withkey.json" if user_keywords else "prompts/withoutkey.json"
        )
        messages = self._load_prompt_messages(template_path)

        for msg in messages:
            content: str = msg["content"]

            if "<news_data_placeholder>" in content:
                content = content.replace("<news_data_placeholder>", str(news_data))

            if user_keywords and "<user_keywords_placeholder>" in content:
                content = content.replace("<user_keywords_placeholder>", user_keywords)

            if "{news_format}" in content:
                content = content.replace("{news_format}", self._news_format)

            if "{news_number}" in content:
                content = content.replace(
                    "{news_number}", str(self._settings.max_news_results)
                )

            msg["content"] = content

        return messages

    def _invoke_llm_sync(
        self,
        llm: HuggingFaceEndpoint,
        messages: list[dict],
    ) -> str:
        template = "Question: {question}\nAnswer: Let's think step by step."
        prompt = PromptTemplate.from_template(template)
        chain = LLMChain(prompt=prompt, llm=llm)
        output = chain.invoke(messages)
        return output.get("text", "")

    
    def _parse_llm_output(self, raw_output: str) -> list[NewsItem]:
        
        if not raw_output or not raw_output.strip():
            return []

        news_items: list[NewsItem] = []

        for line in raw_output.strip().splitlines():
            line = line.strip()
            if not line:
                continue

            if "[" not in line and "," not in line:
                continue

            cleaned = line.rstrip(";").strip()
            if cleaned.startswith("["):
                cleaned = cleaned[1:]
            if cleaned.endswith("]"):
                cleaned = cleaned[:-1]
            cleaned = cleaned.strip()
            if not cleaned:
                continue

            parts = [p.strip().strip("\"'") for p in cleaned.rsplit(",", maxsplit=3)]

            if len(parts) < 2:
                continue

            try:
                item = NewsItem(
                    title=parts[0] if len(parts) > 0 else "No title provided",
                    source=parts[1] if len(parts) > 1 else "No source provided",
                    date=parts[2] if len(parts) > 2 else "No date provided",
                    url=parts[3] if len(parts) > 3 else "No URL provided",
                )
                news_items.append(item)
            except Exception as exc:        
                logger.warning("Skipping unparseable line %r – %s", line, exc)

        return news_items

   
    async def get_news(
        self,
        llm_name: str,
        keywords: Optional[str] = None,
    ) -> NewsResponse:
        
        llm = self._get_llm(llm_name)
        try:
            news_data: list[dict] = await asyncio.to_thread(
                self._repository.get_news_collections
            )
        except Exception as exc:
            logger.error("Pinecone fetch failed: %s", exc)
            raise NewsFetchError(f"Knowledge-base query failed: {exc}") from exc

        news_data = news_data[: self._settings.max_news_context]

        if not news_data:
            return NewsResponse(llm=llm_name, keywords=keywords, count=0, news=[])

        messages = self._build_messages(news_data, keywords)

        try:
            raw_text: str = await asyncio.to_thread(
                self._invoke_llm_sync, llm, messages
            )
        except Exception as exc:
            logger.error("LLM invocation failed: %s", exc)
            raise LLMProcessingError(
                f"LLM '{llm_name}' processing failed: {exc}"
            ) from exc

        news_items = self._parse_llm_output(raw_text)

        return NewsResponse(
            llm=llm_name,
            keywords=keywords,
            count=len(news_items),
            news=news_items,
        )