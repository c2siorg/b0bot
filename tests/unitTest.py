"""
Unit tests for B0Bot Flask routes.

Fixes from original unitTest.py:
1. Routes corrected to match actual Blueprint definitions in NewsRoutes.py
2. Pinecone, HuggingFaceEndpoint and LLMChain all mocked before app import
3. Edge cases added: empty keyword, special characters, long input
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# ── Mock ALL external services before importing app ──────────────────────────
_mock_pinecone = MagicMock()
sys.modules['pinecone'] = MagicMock(Pinecone=MagicMock(return_value=_mock_pinecone))

_mock_llm_chain = MagicMock(return_value=MagicMock(invoke=MagicMock(return_value={"text": ""})))
sys.modules['langchain_community'] = MagicMock()
sys.modules['langchain_community.llms'] = MagicMock(HuggingFaceEndpoint=MagicMock())
sys.modules['langchain_classic'] = MagicMock()
sys.modules['langchain_classic.chains'] = MagicMock(LLMChain=_mock_llm_chain)
sys.modules['langchain_classic.prompts'] = MagicMock()
# ─────────────────────────────────────────────────────────────────────────────

from dotenv import load_dotenv

current_file_path = os.path.abspath(__file__)
src_directory = os.path.dirname(os.path.dirname(current_file_path))
sys.path.append(src_directory)
load_dotenv(os.path.join(src_directory, ".env"))

from app import app

MOCK_NEWS = [
    {"title": "CVE-2024-001 affects Linux kernel", "url": "https://example.com/1"},
    {"title": "Ransomware targets healthcare sector", "url": "https://example.com/2"},
]


class TestRawNewsRoutes(unittest.TestCase):
    """Tests for /raw/news and /raw/news_keywords (no LLM involved)."""

    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    @patch("services.NewsService.CybernewsDB")
    def test_raw_news_returns_200(self, mock_db):
        """GET /raw/news should return HTTP 200."""
        mock_db.return_value.get_news_collections.return_value = MOCK_NEWS
        response = self.client.get("/raw/news")
        self.assertEqual(response.status_code, 200)

    @patch("services.NewsService.CybernewsDB")
    def test_raw_news_response_not_empty(self, mock_db):
        """GET /raw/news should return a non-empty response body."""
        mock_db.return_value.get_news_collections.return_value = MOCK_NEWS
        response = self.client.get("/raw/news")
        self.assertGreater(len(response.data), 0)

    @patch("services.NewsService.CybernewsDB")
    def test_raw_news_keywords_returns_200(self, mock_db):
        """GET /raw/news_keywords?keywords=firewall should return HTTP 200."""
        mock_db.return_value.get_news_collections.return_value = MOCK_NEWS
        response = self.client.get("/raw/news_keywords?keywords=firewall")
        self.assertEqual(response.status_code, 200)

    @patch("services.NewsService.CybernewsDB")
    def test_raw_news_keywords_ransomware(self, mock_db):
        """GET /raw/news_keywords should work with common cybersecurity terms."""
        mock_db.return_value.get_news_collections.return_value = MOCK_NEWS
        response = self.client.get("/raw/news_keywords?keywords=ransomware")
        self.assertEqual(response.status_code, 200)

    @patch("services.NewsService.CybernewsDB")
    def test_raw_news_keywords_empty_does_not_crash(self, mock_db):
        """Empty keyword should not return 500."""
        mock_db.return_value.get_news_collections.return_value = []
        response = self.client.get("/raw/news_keywords?keywords=")
        self.assertNotEqual(response.status_code, 500,
            "Empty keyword caused unhandled 500 — add input validation.")

    @patch("services.NewsService.CybernewsDB")
    def test_raw_news_keywords_special_chars(self, mock_db):
        """Special characters in keyword should not cause a 500 crash."""
        mock_db.return_value.get_news_collections.return_value = []
        response = self.client.get("/raw/news_keywords?keywords=<script>alert(1)</script>")
        self.assertNotEqual(response.status_code, 500,
            "Special characters in keyword caused unhandled 500.")

    @patch("services.NewsService.CybernewsDB")
    def test_raw_news_keywords_very_long(self, mock_db):
        """A very long keyword should not crash the server."""
        mock_db.return_value.get_news_collections.return_value = []
        response = self.client.get(f"/raw/news_keywords?keywords={'malware' * 100}")
        self.assertNotEqual(response.status_code, 500,
            "Very long keyword caused unhandled 500.")


class TestLLMNewsRoutes(unittest.TestCase):
    """Tests for /<llm_name>/news and /<llm_name>/news_keywords."""

    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    @patch("services.NewsService.CybernewsDB")
    def test_llm_news_returns_200(self, mock_db):
        """GET /mistralai/news should return HTTP 200 with mocked LLM."""
        mock_db.return_value.get_news_collections.return_value = MOCK_NEWS
        response = self.client.get("/mistralai/news")
        self.assertEqual(response.status_code, 200)

    @patch("services.NewsService.CybernewsDB")
    def test_llm_news_keywords_returns_200(self, mock_db):
        """GET /mistralai/news_keywords?keywords=malware should return 200."""
        mock_db.return_value.get_news_collections.return_value = MOCK_NEWS
        response = self.client.get("/mistralai/news_keywords?keywords=malware")
        self.assertEqual(response.status_code, 200)


class TestHomeAndMiscRoutes(unittest.TestCase):
    """Tests for home page and edge-case routes."""

    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_home_returns_200(self):
        """GET / should return HTTP 200."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_favicon_returns_204(self):
        """GET /favicon.ico should return 204 No Content."""
        response = self.client.get("/favicon.ico")
        self.assertEqual(response.status_code, 204)

    def test_invalid_deep_route_returns_404(self):
        """
        Multi-segment invalid route should return 404.
        NOTE: /xxx matches /<llm_name> blueprint route — use a
        multi-segment path that cannot match any defined route.
        """
        response = self.client.get("/this/route/does/not/exist/xyz")
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
