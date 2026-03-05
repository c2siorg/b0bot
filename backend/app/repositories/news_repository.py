from __future__ import annotations

import logging
import time

from pinecone import Pinecone, ServerlessSpec
from pinecone.exceptions import NotFoundException

from app.config import Settings

logger = logging.getLogger(__name__)


class NewsRepository:

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = Pinecone(api_key=settings.pinecone_api_key)
        self._namespace = settings.pinecone_namespace
        self._vector_dim = settings.pinecone_vector_dimension
   
        self._index = None

    def _get_index(self):
       
        if self._index is not None:
            return self._index

        index_name = self._settings.pinecone_index_name

        existing = [idx.name for idx in self._client.list_indexes()]

        if index_name not in existing:
            logger.warning(
                "Pinecone index '%s' not found — creating it now …", index_name
            )
            self._client.create_index(
                name=index_name,
                dimension=self._vector_dim,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1"),
            )
           
            while True:
                desc = self._client.describe_index(index_name)
                if getattr(desc.status, "ready", False):
                    break
                logger.info("Waiting for index '%s' to be ready …", index_name)
                time.sleep(2)

            logger.info("Index '%s' is ready.", index_name)

        self._index = self._client.Index(index_name)
        return self._index

   
    def fetch_all_from_namespace(self, batch_size: int = 100) -> list[dict]:
        index = self._get_index()

        id_list: list[str] = []
        for ids in index.list(namespace=self._namespace):
            id_list.extend(ids)

        logger.info("Pinecone: collected %d vector IDs", len(id_list))

        if not id_list:
            logger.warning(
                "Pinecone: no vectors in namespace '%s'. "
                "Run db_update/Update.py to populate the index.",
                self._namespace,
            )
            return []

        results: list[dict] = []

        for i in range(0, len(id_list), batch_size):
            batch_ids = id_list[i : i + batch_size]
            fetch_resp = index.fetch(
                ids=batch_ids, namespace=self._namespace
            )
            
            vectors = fetch_resp.vectors or {}
            for vec_id, vector in vectors.items():
                metadata = getattr(vector, "metadata", None) or {}
                if metadata:
                    results.append(dict(metadata))

        logger.info("Pinecone: fetched metadata for %d articles", len(results))
        return results

    def get_news_collections(self) -> list[dict]:
        return self.fetch_all_from_namespace()

    def search_by_vector(
        self, vector: list[float], top_k: int = 10
    ) -> list[dict]:
        index = self._get_index()
        results = index.query(
            vector=vector,
            top_k=top_k,
            namespace=self._namespace,
            include_metadata=True,
        )
        return [
            dict(match.metadata)
            for match in results.matches
            if match.metadata
        ]