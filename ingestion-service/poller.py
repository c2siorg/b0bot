"""RSS polling and article discovery.

Polls curated cybersecurity RSS feeds on a schedule, normalizes article URLs,
deduplicates by url_hash against the ``processed_jobs`` table, and enqueues
``article.discovered`` jobs onto the Redis BullMQ queue.
"""
import asyncio
import hashlib
import html
import logging
import re
import time
import uuid
from datetime import datetime, timezone
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import feedparser
from bullmq import Queue

from config import (
    ARTICLE_DISCOVERED_QUEUE,
    ARTICLE_SCHEMA_VERSION,
    CONTENT_SNIPPET_MAX_LEN,
    DEFAULT_ARTICLE_LANGUAGE,
    EVENT_ARTICLE_DISCOVERED,
    RSS_FEED_TIMEOUT,
    RSS_USER_AGENT,
    TRACKING_QUERY_PREFIXES,
    article_idempotency_key,
)
from db import fetch_active_sources, get_connection, is_processed
from feeds import RSS_FEEDS

logger = logging.getLogger(__name__)

_TAG_RE = re.compile(r"<[^>]+>")


def clean_text(value: str) -> str:
    """Decode HTML entities and normalize whitespace for RSS text fields."""
    if not value:
        return ""
    return html.unescape(value).strip()


def clean_snippet(value: str) -> str:
    """Decode entities and strip HTML tags from RSS summary/content."""
    text = clean_text(value)
    if not text:
        return ""
    return _TAG_RE.sub("", text).strip()


def load_poll_feeds() -> list[dict]:
    """Load active RSS sources from Postgres, with a hardcoded fallback."""
    try:
        with get_connection() as conn:
            feeds = fetch_active_sources(conn)
        if feeds:
            logger.info("loaded %d active source(s) from database", len(feeds))
            return feeds
    except Exception:
        logger.exception("failed loading sources from database")

    logger.warning("no active sources in database — falling back to RSS_FEEDS")
    return RSS_FEEDS


def normalize_url(url: str) -> str:
    """Normalize an article URL for stable deduplication.

    - Lowercase the domain
    - Strip fragment
    - Remove tracking query params (utm_*, fbclid, gclid, etc.)
    """
    parts = urlsplit(url.strip())
    scheme = parts.scheme.lower()
    netloc = parts.netloc.lower()
    path = parts.path
    fragment = ""
    if parts.query:
        cleaned_query = [
            (key, value)
            for key, value in parse_qsl(parts.query, keep_blank_values=True)
            if not any(key.lower().startswith(prefix) for prefix in TRACKING_QUERY_PREFIXES)
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
    title = clean_text(entry.get("title") or "")
    link = (entry.get("link") or "").strip()
    if not title or not link:
        return None

    normalized = normalize_url(link)
    url_hash = compute_url_hash(normalized)

    snippet = ""
    if entry.get("summary"):
        snippet = entry["summary"]
    elif entry.get("content"):
        content_list = entry["content"]
        if isinstance(content_list, list) and content_list:
            snippet = content_list[0].get("value", "")
        elif isinstance(content_list, str):
            snippet = content_list
    snippet = clean_snippet(snippet)[:CONTENT_SNIPPET_MAX_LEN]

    published_date = None
    if entry.get("published_parsed"):
        try:
            published_date = datetime(*entry["published_parsed"][:6], tzinfo=timezone.utc).isoformat()
        except (TypeError, ValueError):
            published_date = None

    author = clean_text(entry.get("author") or feed.get("author") or "")

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
    idempotency_key = article_idempotency_key(payload["url_hash"])
    return {
        "event_id": str(uuid.uuid4()),
        "event_type": EVENT_ARTICLE_DISCOVERED,
        "trace_id": f"poll-{int(time.time())}",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "idempotency_key": idempotency_key,
        "payload": {
            "schema_version": ARTICLE_SCHEMA_VERSION,
            "source_name": payload["source_name"],
            "feed_url": payload["feed_url"],
            "title": payload["title"],
            "url": payload["url"],
            "url_hash": payload["url_hash"],
            "author": payload["author"],
            "published_at": payload["published_at"],
            "content_snippet": payload["content_snippet"],
            "image_url": payload["image_url"],
            "language": DEFAULT_ARTICLE_LANGUAGE,
        },
    }


def _fetch_feed(feed_url: str) -> list[dict]:
    """Fetch and parse a single RSS feed synchronously.

    feedparser is blocking, so callers should run this in a thread executor.
    Some feeds set bozo=True but still return usable entries (e.g. KrebsOnSecurity).
    """
    parsed = feedparser.parse(
        feed_url,
        request_headers={"User-Agent": RSS_USER_AGENT},
    )
    entry_count = len(parsed.entries)
    if parsed.bozo:
        exc = getattr(parsed, "bozo_exception", "")
        if entry_count:
            logger.warning(
                "feed parse warning for %s (%d entries kept): %s",
                feed_url,
                entry_count,
                exc,
            )
        else:
            logger.warning("feed parse error for %s: %s", feed_url, exc)
            return []
    return parsed.entries


class RssPoller:
    """Polls RSS feeds and enqueues discovered articles."""

    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self._queue = None

    def _get_queue(self) -> Queue:
        if self._queue is None:
            self._queue = Queue(ARTICLE_DISCOVERED_QUEUE, {"connection": self.redis_url})
        return self._queue

    def _already_processed(self, idempotency_key: str) -> bool:
        """Check whether an article has already been processed in Postgres."""
        try:
            with get_connection() as conn:
                return is_processed(conn, idempotency_key)
        except Exception:
            logger.exception("failed checking processed_jobs for %s", idempotency_key)
            return True

    async def poll_all_feeds(self) -> None:
        """Poll every configured RSS feed and enqueue newly discovered articles."""
        feeds = load_poll_feeds()
        logger.info("polling %d RSS feed(s)", len(feeds))
        queue = self._get_queue()
        enqueued = 0
        skipped = 0

        for feed in feeds:
            feed_name = feed["name"]
            feed_enqueued = 0
            feed_skipped = 0
            feed_invalid = 0

            try:
                entries = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(None, _fetch_feed, feed["url"]),
                    timeout=RSS_FEED_TIMEOUT,
                )
            except asyncio.TimeoutError:
                logger.warning("feed timeout (%ss): %s (%s)", RSS_FEED_TIMEOUT, feed_name, feed["url"])
                continue
            except Exception:
                logger.exception("feed fetch failed: %s (%s)", feed_name, feed["url"])
                continue

            if not entries:
                logger.warning("feed returned no entries: %s (%s)", feed_name, feed["url"])
                continue

            for entry in entries:
                parsed = _parse_entry(entry, feed)
                if parsed is None:
                    feed_invalid += 1
                    continue

                idempotency_key = article_idempotency_key(parsed["url_hash"])
                if self._already_processed(idempotency_key):
                    feed_skipped += 1
                    skipped += 1
                    continue

                job_data = _build_job(parsed)
                try:
                    await queue.add(
                        EVENT_ARTICLE_DISCOVERED,
                        job_data,
                        {"jobId": idempotency_key},
                    )
                    feed_enqueued += 1
                    enqueued += 1
                except Exception:
                    logger.exception("failed to enqueue job for %s", parsed["url"])
                    continue

            logger.info(
                "feed %s — entries: %d, enqueued: %d, skipped: %d, invalid: %d",
                feed_name,
                len(entries),
                feed_enqueued,
                feed_skipped,
                feed_invalid,
            )

        logger.info("polling complete — enqueued: %d, skipped (duplicates): %d", enqueued, skipped)

    async def close(self) -> None:
        if self._queue is not None:
            await self._queue.close()
