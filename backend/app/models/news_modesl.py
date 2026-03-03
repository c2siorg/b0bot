from __future__ import annotations

import logging

from pinecone import Pinecone

from app.config import Settings

logger = logging.getLogger(__name__)


class NewsRepository:

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = Pinecone(api_key=settings.pinecone_api_key)
        self._index = self._client.Index(settings.pinecone_index_name)
        self._namespace = settings.pinecone_namespace
        self._vector_dim = settings.pinecone_vector_dimension

    def fetch_all_from_namespace(self, batch_size: int = 100) -> list[dict]:
        
        id_list: list[str] = []
        for ids in self._index.list(namespace=self._namespace):
            id_list.extend(ids)

        logger.info("Pinecone: collected %d vector IDs", len(id_list))

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
        return self.fetch_all_from_namespace()