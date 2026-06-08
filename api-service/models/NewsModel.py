"""Postgres-backed news store.

Replaces the previous Pinecone-backed model. Reads articles from the `articles`
table and returns them in the dict shape the rest of the app already expects
(`headlines`, `author`, `newsDate`, `newsURL`, `newsImgURL`, `fullNews`), so
controllers, services, and the scraper agent need no changes.

Keyword lookups currently use a case-insensitive text filter. Vector similarity
search over the `embedding` column lands once the ingestion service starts
writing embeddings; `search_type` / `alpha` are accepted now to keep that
call signature stable.
"""
import logging

from config.Database import get_connection

logger = logging.getLogger(__name__)

# Map article columns to the dict keys the rest of the app consumes.
# Aliases are quoted to preserve their mixed case through Postgres.
_BASE_SELECT = """
    SELECT
        title                                AS headlines,
        author,
        to_char(published_at, 'DD/MM/YYYY')  AS "newsDate",
        url                                  AS "newsURL",
        image_url                            AS "newsImgURL",
        content                              AS "fullNews"
    FROM articles
"""


class CybernewsDB:
    def get_news_collections(self, is_keyword=False, keyword=None,
                             search_type="hybrid", alpha=0.3, limit=50):
        """Return the most recent articles, optionally filtered by keyword.

        Returns an empty list (and logs) if the database is unreachable, so a
        DB outage degrades the API rather than crashing it.
        """
        try:
            with get_connection() as conn, conn.cursor() as cur:
                if is_keyword and keyword:
                    cur.execute(
                        _BASE_SELECT
                        + " WHERE title ILIKE %(kw)s OR content ILIKE %(kw)s"
                        + " ORDER BY published_at DESC NULLS LAST"
                        + " LIMIT %(limit)s",
                        {"kw": f"%{keyword}%", "limit": limit},
                    )
                else:
                    cur.execute(
                        _BASE_SELECT
                        + " ORDER BY published_at DESC NULLS LAST"
                        + " LIMIT %(limit)s",
                        {"limit": limit},
                    )
                return cur.fetchall()
        except Exception as exc:
            logger.error("Failed to fetch articles from Postgres: %s", exc)
            return []
