import os

import pytest

from feeds import RSS_FEEDS

DEPRECATED_FEED_URLS = {
    "https://us-cert.cisa.gov/mlist.xml",
    "https://www.cisa.gov/news-events/cybersecurity-advisories/all.xml",
}


def test_feed_catalog_has_required_fields():
    assert len(RSS_FEEDS) == 8
    names = set()
    for feed in RSS_FEEDS:
        assert feed.get("name")
        assert feed.get("url", "").startswith("https://")
        assert feed.get("category")
        assert feed["name"] not in names
        names.add(feed["name"])


def test_feed_catalog_excludes_known_broken_urls():
    urls = {feed["url"] for feed in RSS_FEEDS}
    assert urls.isdisjoint(DEPRECATED_FEED_URLS)


@pytest.mark.skipif(
    os.getenv("RUN_FEED_INTEGRATION") != "1",
    reason="set RUN_FEED_INTEGRATION=1 to live-check RSS endpoints",
)
def test_feed_catalog_urls_return_entries():
    import feedparser

    from config import RSS_USER_AGENT

    headers = {"User-Agent": RSS_USER_AGENT}
    failures = []
    for feed in RSS_FEEDS:
        parsed = feedparser.parse(feed["url"], request_headers=headers)
        if not parsed.entries:
            failures.append(f"{feed['name']} ({feed['url']})")

    assert not failures, "feeds with no entries: " + "; ".join(failures)
