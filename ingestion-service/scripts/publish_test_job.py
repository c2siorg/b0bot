"""Push a test article.discovered job onto the queue."""
import asyncio
import hashlib
import os
import uuid
from datetime import datetime, timezone

from bullmq import Queue

QUEUE_NAME = os.getenv("ARTICLE_DISCOVERED_QUEUE", "article-discovered")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

TEST_URL = "https://thehackernews.com/test/queue-worker-sample"


async def main():
    url_hash = hashlib.sha256(TEST_URL.encode()).hexdigest()
    job_data = {
        "event_id": str(uuid.uuid4()),
        "event_type": "article.discovered",
        "trace_id": f"test-{datetime.now(timezone.utc).isoformat()}",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "idempotency_key": f"article:{url_hash}:discovered",
        "payload": {
            "schema_version": 1,
            "source_name": "The Hacker News",
            "feed_url": "https://feeds.feedburner.com/TheHackersNews",
            "title": "Test article from queue worker",
            "url": TEST_URL,
            "url_hash": url_hash,
            "author": "Test Author",
            "published_at": datetime.now(timezone.utc).isoformat(),
            "content_snippet": "Sample content pushed via publish_test_job.py",
            "image_url": None,
            "language": "en",
        },
    }

    queue = Queue(QUEUE_NAME, {"connection": REDIS_URL})
    job = await queue.add("article.discovered", job_data)
    print(f"published job {job.id}")
    await queue.close()


if __name__ == "__main__":
    asyncio.run(main())
