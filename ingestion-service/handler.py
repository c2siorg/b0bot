"""Process article.discovered queue jobs."""
import logging

from db import get_connection, insert_article, is_processed, mark_processed

logger = logging.getLogger(__name__)


def handle_article_discovered(data: dict) -> None:
    event_type = data.get("event_type")
    if event_type != "article.discovered":
        logger.warning("skipping unknown event type: %s", event_type)
        return

    idempotency_key = data["idempotency_key"]
    payload = data["payload"]

    with get_connection() as conn:
        if is_processed(conn, idempotency_key):
            logger.info("already processed: %s", idempotency_key)
            return

        inserted = insert_article(conn, payload)
        mark_processed(conn, idempotency_key, event_type)
        conn.commit()

        if inserted:
            logger.info("inserted article: %s", payload.get("title"))
        else:
            logger.info("duplicate url_hash, skipped insert: %s", payload.get("url_hash"))
