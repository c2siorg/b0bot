"""Postgres-backed source store.
Handles listing and creating RSS sources for the sources page. New sources
are inserted as ``pending``; ingestion-service polls only ``active`` rows.

get_all_sources caches its result in Redis, same pattern as responder.py's
chat response cache. Sources rarely change and the page is read far more
often than it's written to, so caching avoids re-querying every page load.
Cache is invalidated immediately on a successful create_source, rather than
waiting out the TTL, so a newly added source shows up right away.
"""
import json
import logging
import os
import redis
from config.Database import get_connection

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
SOURCES_CACHE_KEY = "sources:all"
SOURCES_CACHE_TTL = 60  # seconds

try:
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
except Exception:
    redis_client = None


class SourceDB:
    def get_all_sources(self) -> list[dict]:
        """Return all sources, newest first. Empty list on any db error."""
        if redis_client:
            try:
                cached = redis_client.get(SOURCES_CACHE_KEY)
                if cached:
                    return json.loads(cached)
            except Exception:
                pass
        try:
            with get_connection() as conn, conn.cursor() as cur:
                cur.execute(
                    "SELECT id, name, url, status, created_at FROM sources ORDER BY created_at DESC"
                )
                sources = cur.fetchall()
        except Exception as exc:
            logger.error("Failed to fetch sources: %s", exc)
            return []
        if redis_client:
            try:
                redis_client.setex(SOURCES_CACHE_KEY, SOURCES_CACHE_TTL, json.dumps(sources, default=str))
            except Exception:
                pass
        return sources

    def create_source(self, name: str, url: str) -> bool | None:
        """Insert a new source as pending. Returns True on success, False if
        the url already exists, None on a real db error."""
        try:
            with get_connection() as conn, conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO sources (name, url, status)
                    VALUES (%(name)s, %(url)s, 'pending')
                    ON CONFLICT (url) DO NOTHING
                    RETURNING id
                    """,
                    {"name": name, "url": url},
                )
                inserted = cur.fetchone() is not None
                conn.commit()
                if inserted and redis_client:
                    try:
                        redis_client.delete(SOURCES_CACHE_KEY)
                    except Exception:
                        pass
                return inserted
        except Exception as exc:
            logger.error("Failed to create source: %s", exc)
            return None
