"""Process article.discovered queue jobs.

For each job: generate an embedding (title + snippet), upsert into the
``articles`` table with pgvector, and mark the job idempotent in
``processed_jobs``. Embedding failures set ``embedding_status=failed``
so the row can be retried later.
"""
import logging

from config import EVENT_ARTICLE_DISCOVERED
from db import get_connection, is_processed, mark_processed, upsert_article
from embeddings import generate_embedding, prepare_embedding_text
from llm_metadata import enrich_metadata_with_llm

logger = logging.getLogger(__name__)


def handle_article_discovered(data: dict) -> None:
    event_type = data.get("event_type")
    if event_type != EVENT_ARTICLE_DISCOVERED:
        logger.warning("skipping unknown event type: %s", event_type)
        return

    idempotency_key = data["idempotency_key"]
    payload = data["payload"]

    with get_connection() as conn:
        if is_processed(conn, idempotency_key):
            logger.info("already processed: %s", idempotency_key)
            return

        # Generate embedding from title + snippet.
        embedding_text = prepare_embedding_text(
            payload.get("title", ""),
            payload.get("content_snippet", ""),
        )
        embedding = generate_embedding(embedding_text)

        if embedding:
            embedding_status = "indexed"
        else:
            embedding_status = "failed"
            logger.warning("embedding failed for article: %s", payload.get("url"))

        metadata = enrich_metadata_with_llm(
            payload.get("title", ""),
            payload.get("content_snippet", ""),
        )
        payload.update(metadata)

        inserted = upsert_article(conn, payload, embedding, embedding_status)
        mark_processed(conn, idempotency_key, event_type)
        conn.commit()

        if inserted:
            logger.info("inserted article: %s", payload.get("title"))
        else:
            logger.info("updated existing article: %s", payload.get("url_hash"))