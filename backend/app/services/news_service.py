"""
Core business-logic layer.

Orchestrates:  Repository (Pinecone) → Prompt building → LLM invocation → Response parsing.

The HuggingFaceEndpoint / LangChain plumbing is deliberately isolated behind
helper methods so that it can be replaced by a LangGraph multi-agent pipeline
in Phase 2 without touching the router or the repository.
"""

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
    """
    Stateful service – instantiated **once** during the app lifespan and
    injected into route handlers via ``Depends(get_news_service)``.

    LLM instances are lazily created and cached by model name so that
    repeated requests for the same LLM do not pay the init cost again.
    """

    def __init__(self, repository: NewsRepository, settings: Settings) -> None:
        self._repository = repository
        self._settings = settings
        self._llm_cache: dict[str, HuggingFaceEndpoint] = {}
        self._llm_config: dict[str, str] = self._load_llm_config()
        self._news_format = "[title, source, date(DD/MM/YYYY), news url];"

        # Required by langchain_community's HuggingFace integration
        os.environ["HUGGINGFACEHUB_API_TOKEN"] = settings.huggingface_token

    # ── Configuration helpers ─────────────────────────────────────────────────

    def _load_llm_config(self) -> dict[str, str]:
        """Load ``{ short_name: huggingface_repo_id }`` from the JSON file."""
        with open(self._settings.llm_config_path, "r", encoding="utf-8") as fh:
            return json.load(fh)

    @property
    def available_models(self) -> list[str]:
        """Short-names that can be used as ``llm_name`` path parameters."""
        return list(self._llm_config.keys())

    # ── LLM factory (cached) ─────────────────────────────────────────────────

    def _get_llm(self, model_name: str) -> HuggingFaceEndpoint:
        """
        Return a (possibly cached) ``HuggingFaceEndpoint`` for *model_name*.

        Raises ``LLMNotFoundError`` if *model_name* is not in the config.
        """
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

    # ── Prompt construction ───────────────────────────────────────────────────

    @staticmethod
    def _load_prompt_messages(path: str) -> list[dict]:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)

    def _build_messages(
        self,
        news_data: list[dict],
        user_keywords: Optional[str] = None,
    ) -> list[dict]:
        """
        Load the appropriate prompt template (with/without keywords),
        fill in placeholders, and return the final messages list.
        """
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

    # ── LLM invocation ────────────────────────────────────────────────────────
    # NOTE (Phase 2): replace this method body with a LangGraph agent call.

    def _invoke_llm_sync(
        self,
        llm: HuggingFaceEndpoint,
        messages: list[dict],
    ) -> str:
        """
        Synchronous LLM call via LangChain's ``LLMChain``.

        Kept as a **blocking** helper so it can be offloaded to a thread
        by the async public method.
        """
        template = "Question: {question}\nAnswer: Let's think step by step."
        prompt = PromptTemplate.from_template(template)
        chain = LLMChain(prompt=prompt, llm=llm)
        output = chain.invoke(messages)
        return output.get("text", "")

    # ── Response parsing ──────────────────────────────────────────────────────

    def _parse_llm_output(self, raw_output: str) -> list[NewsItem]:
        """
        Convert the raw text returned by the LLM into validated
        ``NewsItem`` objects.

        Expected LLM line format::

            [Title, Source, DD/MM/YYYY, https://…];

        Lines that cannot be parsed are silently skipped (logged at WARNING).
        """
        if not raw_output or not raw_output.strip():
            return []

        news_items: list[NewsItem] = []

        for line in raw_output.strip().splitlines():
            line = line.strip()
            if not line:
                continue

            # Quick heuristic: skip preamble / conversational lines
            if "[" not in line and "," not in line:
                continue

            # Strip trailing semicolons and outer brackets
            cleaned = line.rstrip(";").strip()
            if cleaned.startswith("["):
                cleaned = cleaned[1:]
            if cleaned.endswith("]"):
                cleaned = cleaned[:-1]
            cleaned = cleaned.strip()
            if not cleaned:
                continue

            # rsplit keeps titles with commas intact; URL is always last
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
            except Exception as exc:          # noqa: BLE001
                logger.warning("Skipping unparseable line %r – %s", line, exc)

        return news_items

    # ── Public API ────────────────────────────────────────────────────────────

    async def get_news(
        self,
        llm_name: str,
        keywords: Optional[str] = None,
    ) -> NewsResponse:
        """
        End-to-end pipeline:
        1. Validate the requested LLM.
        2. Fetch news articles from Pinecone (blocking → thread-pool).
        3. Build the prompt.
        4. Invoke the LLM (blocking → thread-pool).
        5. Parse the raw text into ``NewsItem`` objects.
        6. Return a validated ``NewsResponse``.
        """
        # 1 ── validate & obtain LLM handle
        llm = self._get_llm(llm_name)

        # 2 ── fetch from knowledge-base (sync Pinecone client)
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

        # 3 ── build prompt
        messages = self._build_messages(news_data, keywords)

        # 4 ── invoke LLM (sync client → offload to thread-pool)
        try:
            raw_text: str = await asyncio.to_thread(
                self._invoke_llm_sync, llm, messages
            )
        except Exception as exc:
            logger.error("LLM invocation failed: %s", exc)
            raise LLMProcessingError(
                f"LLM '{llm_name}' processing failed: {exc}"
            ) from exc

        # 5 ── parse
        news_items = self._parse_llm_output(raw_text)

        # 6 ── respond
        return NewsResponse(
            llm=llm_name,
            keywords=keywords,
            count=len(news_items),
            news=news_items,
        )