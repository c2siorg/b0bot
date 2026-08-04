"""Postgres helpers for the ingestion worker."""
from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row

from config import DATABASE_URL

try:
    from pgvector.psycopg import register_vector
except ImportError:
    register_vector = None


@contextmanager
def get_connection():
    conn = psycopg.connect(DATABASE_URL, row_factory=dict_row)
    try:
        if register_vector is not None:
            register_vector(conn)
        yield conn
    finally:
        conn.close()


def is_processed(conn, idempotency_key: str) -> bool:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT 1 FROM processed_jobs WHERE idempotency_key = %s",
            (idempotency_key,),
        )
        return cur.fetchone() is not None


def mark_processed(conn, idempotency_key: str, event_type: str) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO processed_jobs (idempotency_key, event_type)
            VALUES (%s, %s)
            ON CONFLICT (idempotency_key) DO NOTHING
            """,
            (idempotency_key, event_type),
        )


def upsert_article(conn, payload: dict, embedding=None, embedding_status: str = "pending") -> bool:
    """Insert or update an article row.

    If a row with the same ``url_hash`` already exists, the embedding and
    embedding_status columns are updated (ON CONFLICT DO UPDATE). When an
    embedding is provided, ``embedding_status`` should be ``"indexed"`` or
    ``"failed"``.

    Returns True if a new row was inserted (False means it was an update).
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO articles (
                url, url_hash, title, content, author,
                source_name, feed_url, image_url, published_at,
                cve_id, severity, affected_system, topic_tags,
                embedding_status, embedding
            )
            VALUES (
                %(url)s, %(url_hash)s, %(title)s, %(content)s, %(author)s,
                %(source_name)s, %(feed_url)s, %(image_url)s, %(published_at)s,
                %(cve_id)s, %(severity)s, %(affected_system)s, %(topic_tags)s,
                %(embedding_status)s, %(embedding)s
            )
            ON CONFLICT (url_hash) DO UPDATE SET
                cve_id = COALESCE(EXCLUDED.cve_id, articles.cve_id),
                severity = COALESCE(EXCLUDED.severity, articles.severity),
                affected_system = COALESCE(EXCLUDED.affected_system, articles.affected_system),
                topic_tags = CASE
                    WHEN cardinality(EXCLUDED.topic_tags) > 0 THEN EXCLUDED.topic_tags
                    ELSE articles.topic_tags
                END,
                embedding = EXCLUDED.embedding,
                embedding_status = EXCLUDED.embedding_status,
                updated_at = NOW()
            RETURNING (xmax = 0) AS inserted
            """,
            {
                "url": payload["url"],
                "url_hash": payload["url_hash"],
                "title": payload["title"],
                "content": payload.get("content_snippet", ""),
                "author": payload.get("author"),
                "source_name": payload["source_name"],
                "feed_url": payload.get("feed_url"),
                "image_url": payload.get("image_url"),
                "published_at": payload.get("published_at"),
                "cve_id": payload.get("cve_id"),
                "severity": payload.get("severity"),
                "affected_system": payload.get("affected_system"),
                "topic_tags": payload.get("topic_tags") or [],
                "embedding_status": embedding_status,
                "embedding": embedding,
            },
        )
        row = cur.fetchone()
        return bool(row and row.get("inserted"))
