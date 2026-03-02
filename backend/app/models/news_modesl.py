"""
Data-access layer for the Pinecone vector store.

Mirrors the query logic from the legacy ``models/NewsModel.py`` but is
decoupled from global state and accepts its configuration via DI.
"""

from __future__ import annotations

import logging

from pinecone import Pinecone

from app.config import Settings

logger = logging.getLogger(__name__)


class NewsRepository:
    """
    Thin wrapper around the Pinecone index that knows how to retrieve
    all article metadata from a given namespace.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = Pinecone(api_key=settings.pinecone_api_key)
        self._index = self._client.Index(settings.pinecone_index_name)
        self._namespace = settings.pinecone_namespace
        self._vector_dim = settings.pinecone_vector_dimension

    # ──────────────────────────────────────────────────────────────────────────

    def fetch_all_from_namespace(self, batch_size: int = 100) -> list[dict]:
        """
        Retrieve **all** article metadata stored under ``self._namespace``.

        Strategy (unchanged from legacy code):
        1. Query with a zero-vector to collect all IDs (paginated).
        2. Fetch full records by ID and extract their ``metadata`` dicts.
        """
        zero_vector = [0.0] * self._vector_dim

        # ── Step 1: collect IDs ───────────────────────────────────────────────
        id_list: list[str] = []
        cursor: str | None = None

        while True:
            response = self._index.query(
                vector=zero_vector,
                namespace=self._namespace,
                top_k=batch_size,
                include_metadata=False,
                include_values=False,
            )
            ids = [match["id"] for match in response.get("matches", [])]
            id_list.extend(ids)

            cursor = response.get("next_cursor")
            if not cursor:
                break

        logger.info("Pinecone: collected %d vector IDs", len(id_list))

        # ── Step 2: fetch metadata ───────────────────────────────────────────
        results: list[dict] = []

        for i in range(0, len(id_list), batch_size):
            batch_ids = id_list[i : i + batch_size]
            fetch_resp = self._index.fetch(
                ids=batch_ids, namespace=self._namespace
            )
            vectors = fetch_resp.get("vectors", {})
            for vec_id in vectors:
                metadata = vectors[vec_id].get("metadata", {})
                if metadata:
                    results.append(metadata)

        logger.info("Pinecone: fetched metadata for %d articles", len(results))
        return results

    def get_news_collections(self) -> list[dict]:
        """Public convenience alias used by the service layer."""
        return self.fetch_all_from_namespace()