"""Postgres-backed news store.

Replaces the previous Pinecone-backed model. Reads articles from the `articles`
table and returns them in the dict shape the rest of the app already expects
(`headlines`, `author`, `newsDate`, `newsURL`, `newsImgURL`, `fullNews`), so
controllers, services, and the scraper agent need no changes.

Keyword lookups use Postgres full-text search (ts_rank). When a query_vector
is provided, results are ranked by a weighted blend of text relevance and
cosine similarity against the embedding column, controlled by alpha. Falls
back to a plain ILIKE filter when search_type/query_vector are not used, so
the legacy NewsService caller is unaffected.
"""
import logging

from config.Database import get_connection

try:
    from pgvector.psycopg import register_vector
except ImportError:
    register_vector = None

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

_HYBRID_SELECT = """
    SELECT
        title                                AS headlines,
        author,
        to_char(published_at, 'DD/MM/YYYY')  AS "newsDate",
        url                                  AS "newsURL",
        image_url                            AS "newsImgURL",
        content                              AS "fullNews"
    FROM articles
    WHERE embedding IS NOT NULL
    ORDER BY
        %(alpha)s * ts_rank(to_tsvector('english', title || ' ' || content), plainto_tsquery('english', %(kw)s))
        + (1 - %(alpha)s) * (1 - (embedding <=> %(query_vector)s::vector)) DESC
    LIMIT %(limit)s
"""


class CybernewsDB:
    def get_news_collections(self, is_keyword=False, keyword=None,
                             search_type="hybrid", alpha=0.3, limit=50,
                             query_vector=None):
        """Return the most recent articles, optionally filtered by keyword.

        When query_vector is provided alongside a keyword, uses hybrid
        ranking (text relevance + vector similarity, weighted by alpha).
        Returns an empty list (and logs) if the database is unreachable, so a
        DB outage degrades the API rather than crashing it.
        """
        try:
            with get_connection() as conn, conn.cursor() as cur:
                if register_vector is not None:
                    register_vector(conn)
                if is_keyword and keyword and query_vector:
                    cur.execute(
                        _HYBRID_SELECT,
                        {
                            "kw": keyword,
                            "alpha": alpha,
                            "query_vector": query_vector,
                            "limit": limit,
                        },
                    )
                elif is_keyword and keyword:
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
