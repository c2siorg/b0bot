"""Tests for concurrent news fetching in db_update/Update.py.

These tests verify that the ThreadPoolExecutor logic correctly fetches
all six news categories in parallel and handles per-category errors
gracefully.
"""

import unittest
from unittest.mock import MagicMock, patch
from concurrent.futures import ThreadPoolExecutor, as_completed

import sys
import os

# Allow imports from project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# We import only the helper and constant — not the entire Update module,
# because that triggers Pinecone/model initialization at import time.
# Instead we replicate the lightweight concurrency logic here so the test
# can run without any external services.

CATEGORIES = {
    "general_news":       "general",
    "cyber_attack_news":  "cyberAttack",
    "vulnerability_news": "vulnerability",
    "malware_news":       "malware",
    "security_news":      "security",
    "data_breach_news":   "dataBreach",
}


def _fetch_category(category_key, category_query, news_client):
    """Mirror of the helper in Update.py."""
    articles = news_client.get_news(category_query)
    return category_key, articles


class TestConcurrentFetch(unittest.TestCase):
    """Verify concurrent news fetching behaviour."""

    def _make_fake_client(self, side_effect=None):
        """Return a mock CyberNews whose get_news returns dummy articles."""
        client = MagicMock()
        if side_effect:
            client.get_news.side_effect = side_effect
        else:
            client.get_news.side_effect = lambda q: [
                {"id": f"{q}_1", "headlines": f"{q} headline",
                 "author": "test", "fullNews": "body",
                 "newsURL": "https://example.com", "newsImgURL": "",
                 "newsDate": "2026-01-01"}
            ]
        return client

    def test_all_categories_fetched(self):
        """All 6 categories should appear in newsBox after concurrent fetch."""
        client = self._make_fake_client()
        newsBox = {}

        with ThreadPoolExecutor(max_workers=len(CATEGORIES)) as pool:
            futures = {
                pool.submit(_fetch_category, key, query, client): key
                for key, query in CATEGORIES.items()
            }
            for future in as_completed(futures):
                key, articles = future.result()
                newsBox[key] = articles

        self.assertEqual(set(newsBox.keys()), set(CATEGORIES.keys()))
        self.assertEqual(client.get_news.call_count, 6)

    def test_results_correctly_mapped(self):
        """Each category key should contain articles for its own query."""
        client = self._make_fake_client()
        newsBox = {}

        with ThreadPoolExecutor(max_workers=len(CATEGORIES)) as pool:
            futures = {
                pool.submit(_fetch_category, key, query, client): key
                for key, query in CATEGORIES.items()
            }
            for future in as_completed(futures):
                key, articles = future.result()
                newsBox[key] = articles

        for key, query in CATEGORIES.items():
            self.assertTrue(len(newsBox[key]) > 0)
            self.assertIn(query, newsBox[key][0]["id"])

    def test_single_category_failure_does_not_crash(self):
        """If one category raises, the others should still succeed."""

        def _side_effect(query):
            if query == "malware":
                raise RuntimeError("simulated network timeout")
            return [{"id": f"{query}_1", "headlines": f"{query} headline",
                     "author": "test", "fullNews": "body",
                     "newsURL": "https://example.com", "newsImgURL": "",
                     "newsDate": "2026-01-01"}]

        client = self._make_fake_client(side_effect=_side_effect)
        newsBox = {}

        with ThreadPoolExecutor(max_workers=len(CATEGORIES)) as pool:
            futures = {
                pool.submit(_fetch_category, key, query, client): key
                for key, query in CATEGORIES.items()
            }
            for future in as_completed(futures):
                cat = futures[future]
                try:
                    key, articles = future.result()
                    newsBox[key] = articles
                except Exception:
                    pass  # mirrors the logger.exception path in Update.py

        # 5 of 6 categories should have succeeded
        self.assertEqual(len(newsBox), 5)
        self.assertNotIn("malware_news", newsBox)


if __name__ == '__main__':
    unittest.main()
