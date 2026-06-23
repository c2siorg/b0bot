"""Ingestion service entrypoint.

Consumes article.discovered jobs from the Redis BullMQ queue and writes
them into Postgres. RSS polling and embedding land in later weeks.
"""
import asyncio
import logging
import os
import signal

from bullmq import Worker

from handler import handle_article_discovered

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("ingestion-service")

QUEUE_NAME = os.getenv("ARTICLE_DISCOVERED_QUEUE", "article-discovered")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")


async def process_job(job, job_token):
    handle_article_discovered(job.data)


async def main():
    shutdown = asyncio.Event()

    def handle_signal(sig, frame):
        logger.info("shutting down")
        shutdown.set()

    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    logger.info("listening on queue %s", QUEUE_NAME)
    worker = Worker(QUEUE_NAME, process_job, {"connection": REDIS_URL})

    await shutdown.wait()

    logger.info("closing worker")
    await worker.close()


if __name__ == "__main__":
    asyncio.run(main())
