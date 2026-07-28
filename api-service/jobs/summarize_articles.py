"""Batch job that fills in missing article summaries.

Reads articles where summary IS NULL, generates a summary for each via
services.summarizer.generate_summary, and writes it back. Each article
is isolated in its own try/except so one failure (bad content, a
transient Cohere/HF outage) doesn't stop the rest of the batch, articles
that fail stay NULL and get picked up again on the next run.

Standalone entrypoint, same shape as notification-service/worker.py and
ingestion-service/worker.py, run directly rather than imported:
    python3 -m jobs.summarize_articles
"""
import logging
import os

from dotenv import load_dotenv

load_dotenv()

from config.Database import get_connection
from services.summarizer import generate_summary

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("summarize-articles")

BATCH_SIZE = int(os.getenv("SUMMARY_BATCH_SIZE", "50"))


def _fetch_pending_articles(conn, limit: int) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, content
            FROM articles
            WHERE summary IS NULL
            ORDER BY ingested_at DESC
            LIMIT %(limit)s
            """,
            {"limit": limit},
        )
        return cur.fetchall()


def _save_summary(conn, article_id, summary: str) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE articles
            SET summary = %(summary)s, updated_at = NOW()
            WHERE id = %(article_id)s
            """,
            {"summary": summary, "article_id": article_id},
        )
    conn.commit()


def run_once() -> None:
    with get_connection() as conn:
        articles = _fetch_pending_articles(conn, BATCH_SIZE)
        if not articles:
            logger.info("no articles pending summarization")
            return

        logger.info("summarizing %d articles", len(articles))
        succeeded = 0
        for article in articles:
            article_id = article["id"]
            try:
                summary = generate_summary(article["content"])
                if not summary:
                    logger.warning("no summary produced for article %s, will retry next run", article_id)
                    continue
                _save_summary(conn, article_id, summary)
                succeeded += 1
            except Exception:
                conn.rollback()
                logger.exception("failed to summarize article %s", article_id)

        logger.info("summarized %d/%d articles", succeeded, len(articles))


if __name__ == "__main__":
    run_once()
