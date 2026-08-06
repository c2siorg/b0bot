"""Postgres-backed source store.
Handles listing and creating RSS sources for the sources page. New sources
are inserted as 'pending' since ingestion-service still reads from the
hardcoded RSS_FEEDS list in ingestion-service/feeds.py, not this table yet.
"""
import logging
from config.Database import get_connection

logger = logging.getLogger(__name__)


class SourceDB:
    def get_all_sources(self) -> list[dict]:
        """Return all sources, newest first. Empty list on any db error."""
        try:
            with get_connection() as conn, conn.cursor() as cur:
                cur.execute(
                    "SELECT id, name, url, status, created_at FROM sources ORDER BY created_at DESC"
                )
                return cur.fetchall()
        except Exception as exc:
            logger.error("Failed to fetch sources: %s", exc)
            return []

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
                return inserted
        except Exception as exc:
            logger.error("Failed to create source: %s", exc)
            return None
