"""Postgres helpers for the ingestion worker."""
import os
from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://b0bot:b0bot@localhost:5432/b0bot",
)


@contextmanager
def get_connection():
    conn = psycopg.connect(DATABASE_URL, row_factory=dict_row)
    try:
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


def insert_article(conn, payload: dict) -> bool:
    """Insert an article row. Returns True if a new row was inserted."""
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO articles (
                url, url_hash, title, content, author,
                source_name, feed_url, image_url, published_at,
                embedding_status
            )
            VALUES (
                %(url)s, %(url_hash)s, %(title)s, %(content)s, %(author)s,
                %(source_name)s, %(feed_url)s, %(image_url)s, %(published_at)s,
                'pending'
            )
            ON CONFLICT (url_hash) DO NOTHING
            RETURNING id
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
            },
        )
        return cur.fetchone() is not None
