"""Ingestion service entrypoint.

Runs two concurrent tasks:
1. RSS poller — fetches cybersecurity feeds every POLLING_INTERVAL_SECONDS,
   deduplicates by url_hash, and enqueues article.discovered jobs.
2. BullMQ worker — consumes article.discovered jobs, generates embeddings,
   and upserts into Postgres + pgvector.
"""
import asyncio
import logging
import os
import signal

from bullmq import Worker

from handler import handle_article_discovered
from poller import RssPoller

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("ingestion-service")

QUEUE_NAME = os.getenv("ARTICLE_DISCOVERED_QUEUE", "article-discovered")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
POLLING_INTERVAL_SECONDS = int(os.getenv("POLLING_INTERVAL_SECONDS", "900"))


async def process_job(job, job_token):
    handle_article_discovered(job.data)


async def run_poller(shutdown: asyncio.Event):
    """Run the RSS poller on a fixed interval until shutdown."""
    poller = RssPoller(REDIS_URL)
    # Run an initial poll immediately on startup, then on interval.
    while not shutdown.is_set():
        try:
            await poller.poll_all_feeds()
        except Exception:
            logger.exception("polling cycle failed")
        try:
            await asyncio.wait_for(shutdown.wait(), timeout=POLLING_INTERVAL_SECONDS)
        except asyncio.TimeoutError:
            pass


async def main():
    shutdown = asyncio.Event()

    def handle_signal(sig, frame):
        logger.info("shutting down")
        shutdown.set()

    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    logger.info("listening on queue %s", QUEUE_NAME)
    worker = Worker(QUEUE_NAME, process_job, {"connection": REDIS_URL})

    logger.info("starting RSS poller (interval: %ss)", POLLING_INTERVAL_SECONDS)
    poller_task = asyncio.create_task(run_poller(shutdown))

    await shutdown.wait()

    logger.info("closing worker")
    await worker.close()
    poller_task.cancel()
    try:
        await poller_task
    except asyncio.CancelledError:
        pass


if __name__ == "__main__":
    asyncio.run(main())
