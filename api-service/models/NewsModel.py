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
        content                              AS "fullNews",
        summary
    FROM articles
"""

_HYBRID_SELECT = """
    SELECT
        title                                AS headlines,
        author,
        to_char(published_at, 'DD/MM/YYYY')  AS "newsDate",
        url                                  AS "newsURL",
        image_url                            AS "newsImgURL",
        content                              AS "fullNews",
        summary
    FROM articles
    WHERE embedding IS NOT NULL
    ORDER BY
        %(alpha)s * ts_rank(to_tsvector('english', title || ' ' || content), plainto_tsquery('english', %(kw)s))
        + (1 - %(alpha)s) * (1 - (embedding <=> %(query_vector)s::vector)) DESC
    LIMIT %(limit)s
"""


_TOP_NEWS_SELECT = """
    SELECT
        id::text AS id,
        cve_id,
        severity AS type,
        affected_system AS system,
        to_char(published_at, 'DD-MM-YYYY') AS date
    FROM articles
    ORDER BY ingested_at DESC
    LIMIT %(limit)s
"""

_CVE_WATCHLIST_SELECT = """
    SELECT
        id::text AS id,
        cve_id,
        severity,
        affected_system AS system,
        to_char(published_at, 'DD-MM-YYYY') AS date
    FROM articles
    WHERE cve_id IS NOT NULL
    ORDER BY published_at DESC
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

    def get_dashboard_feed(self, filter="newest", source=None, limit=50) -> list[dict]:
        """Return articles for the dashboard feed. filter must be one of
        'newest', 'critical', 'frequent' - anything else falls back to
        newest. source, if given, restricts to that source_name.
        filter/source never get string-interpolated into SQL directly,
        filter picks a fixed clause template and source is bound as a param.
        """
        where_clauses = []
        params = {"limit": limit}
        if filter == "critical":
            where_clauses.append("severity = 'CRITICAL'")
        if source:
            where_clauses.append("source_name = %(source)s")
            params["source"] = source
        where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
        if filter == "frequent":
            order_sql = """ORDER BY (
                SELECT count(*) FROM articles a2 WHERE a2.source_name = articles.source_name
            ) DESC, ingested_at DESC"""
        else:
            order_sql = "ORDER BY ingested_at DESC"
        query = f"""
            SELECT id::text AS id, title, url, summary, source_name,
                   to_char(ingested_at, 'HH24:MI') AS ingested_time
            FROM articles
            {where_sql}
            {order_sql}
            LIMIT %(limit)s
        """
        try:
            with get_connection() as conn, conn.cursor() as cur:
                cur.execute(query, params)
                return cur.fetchall()
        except Exception as exc:
            logger.error("Failed to fetch dashboard feed: %s", exc)
            return []

    def get_distinct_sources(self) -> list[str]:
        """Return distinct source names currently in the articles table, for
        the dashboard's source filter dropdown."""
        try:
            with get_connection() as conn, conn.cursor() as cur:
                cur.execute("SELECT DISTINCT source_name FROM articles ORDER BY source_name")
                return [row["source_name"] for row in cur.fetchall()]
        except Exception as exc:
            logger.error("Failed to fetch distinct sources: %s", exc)
            return []

    def get_top_news(self, limit=5) -> list[dict]:
        """Return the most recent articles for the top news panel, same pool
        as the feed, not filtered to CVEs."""
        try:
            with get_connection() as conn, conn.cursor() as cur:
                cur.execute(_TOP_NEWS_SELECT, {"limit": limit})
                return cur.fetchall()
        except Exception as exc:
            logger.error("Failed to fetch top news: %s", exc)
            return []

    def get_cve_watchlist(self, limit=5) -> list[dict]:
        """Return the most recent articles that have a cve_id set. May be
        sparse - only some articles get cve_id/severity/affected_system
        populated during ingestion, depending on whether the article
        content actually references a CVE."""
        try:
            with get_connection() as conn, conn.cursor() as cur:
                cur.execute(_CVE_WATCHLIST_SELECT, {"limit": limit})
                return cur.fetchall()
        except Exception as exc:
            logger.error("Failed to fetch cve watchlist: %s", exc)
            return []

    def get_article_by_id(self, article_id: str) -> dict | None:
        """Return one article's title, url, content, and summary by id, for
        pre-loading Chat with article context. None if not found or on
        a db error."""
        try:
            with get_connection() as conn, conn.cursor() as cur:
                cur.execute(
                    "SELECT id::text AS id, title, url, content, summary, source_name FROM articles WHERE id = %(id)s",
                    {"id": article_id},
                )
                return cur.fetchone()
        except Exception as exc:
            logger.error("Failed to fetch article %s: %s", article_id, exc)
            return None
