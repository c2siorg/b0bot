"""RSS polling and article discovery.

Polls curated cybersecurity RSS feeds on a schedule, normalizes article URLs,
deduplicates by url_hash against the ``processed_jobs`` table, and enqueues
``article.discovered`` jobs onto the Redis BullMQ queue.
"""
import asyncio
import hashlib
import logging
import os
import time
import uuid
from datetime import datetime, timezone
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import feedparser
from bullmq import Queue
from db import get_connection, is_processed

logger = logging.getLogger(__name__)

QUEUE_NAME = os.getenv("ARTICLE_DISCOVERED_QUEUE", "article-discovered")
RSS_FEED_TIMEOUT = int(os.getenv("RSS_FEED_TIMEOUT", "10"))

# Curated cybersecurity RSS feeds (no API key required).
# Reddit/Mastodon/YouTube connectors are out of scope for GSoC — see .cursorrules.
RSS_FEEDS = [
    {
        "name": "The Hacker News",
        "url": "https://thehackernews.com/feeds/posts/default",
        "category": "Breaking news",
    },
    {
        "name": "KrebsOnSecurity",
        "url": "https://krebsonsecurity.com/feed/",
        "category": "Deep investigations",
    },
    {
        "name": "BleepingComputer",
        "url": "https://www.bleepingcomputer.com/feed/",
        "category": "Malware/incidents",
    },
    {
        "name": "CISA Alerts",
        "url": "https://us-cert.cisa.gov/mlist.xml",
        "category": "Official advisories",
    },
    {
        "name": "CyberScoop",
        "url": "https://www.cyberscoop.com/feed/",
        "category": "Industry analysis",
    },
    {
        "name": "SecurityWeek",
        "url": "https://www.securityweek.com/feed",
        "category": "Weekly roundup",
    },
]

# Tracking query params to strip during normalization.
_TRACKING_PREFIXES = ("utm_", "fbclid", "gclid", "ref", "source")


def normalize_url(url: str) -> str:
    """Normalize an article URL for stable deduplication.

    - Lowercase the domain
    - Strip fragment
    - Remove tracking query params (utm_*, fbclid, gclid, etc.)
    """
    parts = urlsplit(url.strip())
    # Lowercase scheme + netloc.
    scheme = parts.scheme.lower()
    netloc = parts.netloc.lower()
    path = parts.path
    # Drop fragment.
    fragment = ""
    # Filter tracking params.
    if parts.query:
        cleaned_query = [
            (key, value)
            for key, value in parse_qsl(parts.query, keep_blank_values=True)
            if not any(key.lower().startswith(prefix) for prefix in _TRACKING_PREFIXES)
        ]
        query = urlencode(cleaned_query)
    else:
        query = ""
    return urlunsplit((scheme, netloc, path, query, fragment))


def compute_url_hash(normalized_url: str) -> str:
    """SHA-256 hex digest of the normalized URL."""
    return hashlib.sha256(normalized_url.encode("utf-8")).hexdigest()


def _parse_entry(entry: dict, feed: dict) -> dict | None:
    """Parse a feedparser entry into a normalized article payload.

    Returns ``None`` if required fields are missing.
    """
    title = (entry.get("title") or "").strip()
    link = (entry.get("link") or "").strip()
    if not title or not link:
        return None

    normalized = normalize_url(link)
    url_hash = compute_url_hash(normalized)

    # Description / snippet — prefer summary over content.
    snippet = ""
    if entry.get("summary"):
        snippet = entry["summary"]
    elif entry.get("content"):
        content_list = entry["content"]
        if isinstance(content_list, list) and content_list:
            snippet = content_list[0].get("value", "")
        elif isinstance(content_list, str):
            snippet = content_list
    # Trim to a reasonable snippet length.
    snippet = snippet.strip()[:500]

    published_date = None
    if entry.get("published_parsed"):
        try:
            published_date = datetime(*entry["published_parsed"][:6], tzinfo=timezone.utc).isoformat()
        except (TypeError, ValueError):
            published_date = None

    author = entry.get("author") or feed.get("author") or ""

    image_url = None
    if entry.get("media_content"):
        media = entry["media_content"]
        if isinstance(media, list) and media:
            image_url = media[0].get("url")
    elif entry.get("media_thumbnail"):
        media = entry["media_thumbnail"]
        if isinstance(media, list) and media:
            image_url = media[0].get("url")

    return {
        "title": title,
        "url": normalized,
        "url_hash": url_hash,
        "content_snippet": snippet,
        "author": author,
        "source_name": feed["name"],
        "feed_url": feed["url"],
        "image_url": image_url,
        "published_at": published_date,
    }


def _build_job(payload: dict) -> dict:
    """Wrap an article payload in the article.discovered event contract."""
    idempotency_key = f"article:{payload['url_hash']}:discovered"
    return {
        "event_id": str(uuid.uuid4()),
        "event_type": "article.discovered",
        "trace_id": f"poll-{int(time.time())}",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "idempotency_key": idempotency_key,
        "payload": {
            "schema_version": 1,
            "source_name": payload["source_name"],
            "feed_url": payload["feed_url"],
            "title": payload["title"],
            "url": payload["url"],
            "url_hash": payload["url_hash"],
            "author": payload["author"],
            "published_at": payload["published_at"],
            "content_snippet": payload["content_snippet"],
            "image_url": payload["image_url"],
            "language": "en",
        },
    }


def _fetch_feed(feed_url: str) -> list[dict]:
    """Fetch and parse a single RSS feed synchronously.

    feedparser is blocking, so callers should run this in a thread executor.
    """
    parsed = feedparser.parse(feed_url, request_headers={"User-Agent": "B0Bot/1.0"})
    if parsed.bozo and not parsed.entries:
        logger.warning("feed parse error for %s: %s", feed_url, getattr(parsed, "bozo_exception", ""))
        return []
    return parsed.entries


class RssPoller:
    """Polls RSS feeds and enqueues discovered articles."""

    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self._queue = None

    def _get_queue(self) -> Queue:
        if self._queue is None:
            self._queue = Queue(QUEUE_NAME, {"connection": self.redis_url})
        return self._queue

    def _already_processed(self, idempotency_key: str) -> bool:
        """Check whether an article has already been processed in Postgres."""
        try:
            with get_connection() as conn:
                return is_processed(conn, idempotency_key)
        except Exception:
            logger.exception("failed checking processed_jobs for %s", idempotency_key)
            # Fail open — skip enqueue on DB error to avoid duplicate storms.
            return True

    async def poll_all_feeds(self) -> None:
        """Poll every configured RSS feed and enqueue newly discovered articles."""
        logger.info("polling %d RSS feeds", len(RSS_FEEDS))
        queue = self._get_queue()
        enqueued = 0
        skipped = 0

        for feed in RSS_FEEDS:
            try:
                entries = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(None, _fetch_feed, feed["url"]),
                    timeout=RSS_FEED_TIMEOUT,
                )
            except asyncio.TimeoutError:
                logger.warning("feed timeout (%ss): %s", RSS_FEED_TIMEOUT, feed["url"])
                continue
            except Exception:
                logger.exception("feed fetch failed: %s", feed["url"])
                continue

            for entry in entries:
                parsed = _parse_entry(entry, feed)
                if parsed is None:
                    logger.debug("skipping entry with missing title/link in %s", feed["url"])
                    continue

                idempotency_key = f"article:{parsed['url_hash']}:discovered"
                if self._already_processed(idempotency_key):
                    skipped += 1
                    continue

                job_data = _build_job(parsed)
                try:
                    await queue.add(
                        "article.discovered",
                        job_data,
                        {"jobId": idempotency_key},
                    )
                    enqueued += 1
                except Exception:
                    logger.exception("failed to enqueue job for %s", parsed["url"])
                    continue

        logger.info("polling complete — enqueued: %d, skipped (duplicates): %d", enqueued, skipped)

    async def close(self) -> None:
        if self._queue is not None:
            await self._queue.close()