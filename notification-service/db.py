"""Database helpers for notification-service."""

import os
from contextlib import contextmanager
from datetime import datetime

import psycopg
from psycopg.rows import dict_row


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://b0bot:b0bot@postgres:5432/b0bot",
)


@contextmanager
def get_connection():
    conn = psycopg.connect(DATABASE_URL, row_factory=dict_row)
    try:
        yield conn
    finally:
        conn.close()


def get_due_subscribers(conn, now_utc: datetime) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, email, digest_frequency, digest_sent_at
            FROM subscribers
            WHERE status = 'active'
              AND (
                    digest_sent_at IS NULL
                    OR (digest_frequency = 'daily' AND digest_sent_at <= %(now)s - INTERVAL '24 hours')
                    OR (digest_frequency = 'weekly' AND digest_sent_at <= %(now)s - INTERVAL '7 days')
              )
            ORDER BY created_at ASC
            """,
            {"now": now_utc},
        )
        return cur.fetchall() or []


def get_recent_articles(conn, window_start: datetime, limit: int) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, title, url, source_name, severity, published_at, ingested_at
            FROM articles
            WHERE COALESCE(published_at, ingested_at) >= %(window_start)s
            ORDER BY COALESCE(published_at, ingested_at) DESC
            LIMIT %(limit)s
            """,
            {"window_start": window_start, "limit": limit},
        )
        return cur.fetchall() or []


def delivery_exists(conn, idempotency_key: str) -> bool:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT 1 FROM digest_deliveries WHERE idempotency_key = %s",
            (idempotency_key,),
        )
        return cur.fetchone() is not None


def insert_delivery(
    conn,
    *,
    subscriber_id,
    article_ids: list,
    status: str,
    idempotency_key: str,
    provider: str = "smtp",
    error_message: str | None = None,
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO digest_deliveries (
                subscriber_id,
                article_ids,
                provider,
                status,
                error_message,
                idempotency_key
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (subscriber_id, article_ids, provider, status, error_message, idempotency_key),
        )


def update_digest_sent_at(conn, subscriber_id, sent_at: datetime) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE subscribers
            SET digest_sent_at = %s,
                updated_at = NOW()
            WHERE id = %s
            """,
            (sent_at, subscriber_id),
        )
