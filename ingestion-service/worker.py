"""Ingestion service entrypoint.

Polls RSS feeds, deduplicates articles by URL hash, and enqueues
``article.discovered`` jobs for the embedding worker to upsert into
Postgres + pgvector.

This is a scaffold. The polling, dedup, and embedding pipeline land in the
ingestion weeks of the timeline. For now the service starts cleanly and idles,
so it can be wired into the compose stack alongside Postgres and Redis.
"""
import logging
import os
import time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("ingestion-service")

POLL_INTERVAL_SECONDS = int(os.getenv("INGESTION_POLL_INTERVAL", "300"))


def main() -> None:
    logger.info("ingestion-service starting (poll interval: %ss)", POLL_INTERVAL_SECONDS)
    logger.info("RSS polling + queue pipeline not implemented yet — idling")
    while True:
        # Real RSS poll -> dedup by url_hash -> enqueue article.discovered.
        time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
