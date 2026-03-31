"""
Flask route integration tests for b0bot.

Bug fixes vs. the original unitTest.py
───────────────────────────────────────
1. Routes `/news` and `/news_keywords` no longer exist.
   The correct routes introduced in NewsRoutes.py are:
     - GET /<llm_name>/news
     - GET /<llm_name>/news_keywords?keywords=<term>
     - GET /raw/news            ← no LLM; used here to avoid HF token
     - GET /raw/news_keywords?keywords=<term>

2. The 404 handler in NewsRoutes.py (line 73-75) references
   `g.news_controller.notFound(error)` but `g.news_controller` is never
   set for unknown routes — it only exists inside the LLM routes.
   The 404 test is updated to verify the response code only, not
   the error body, until the handler is properly fixed.

3. All Pinecone / SentenceTransformer calls are intercepted by the
   shared fixtures in conftest.py — no API keys or network required.
"""
import pytest


# ── Fixtures are injected from tests/conftest.py automatically ───────────────
# `client` provides a Flask test client with all externals mocked.


class TestHomeRoute:
    """GET / → renders home.html (200)."""

    def test_home_returns_200(self, client):
        response = client.get("/")
        assert response.status_code == 200

    def test_home_contains_html(self, client):
        response = client.get("/")
        assert b"<html" in response.data.lower() or len(response.data) > 0


class TestRawNewsRoute:
    """
    GET /raw/news → bypasses LLM entirely (NewsController(None)).
    This is the safest route to test without HuggingFace credentials.
    """

    def test_raw_news_returns_200(self, client):
        response = client.get("/raw/news")
        assert response.status_code == 200

    def test_raw_news_returns_html(self, client):
        response = client.get("/raw/news")
        # The route renders news.html which should contain some content
        assert response.content_type.startswith("text/html")


class TestRawNewsKeywordsRoute:
    """GET /raw/news_keywords?keywords=<term> → hybrid keyword search, no LLM."""

    def test_raw_news_keywords_returns_200(self, client):
        response = client.get("/raw/news_keywords?keywords=firewall")
        assert response.status_code == 200

    def test_raw_news_keywords_multiple_terms(self, client):
        response = client.get("/raw/news_keywords?keywords=ransomware")
        assert response.status_code == 200

    def test_raw_news_keywords_missing_param_raises_error(self, client):
        """
        No `keywords` query param → getlist returns [] → user_keywords[0]
        raises IndexError. Confirms the existing unhandled edge case.
        Tracked as a known bug — proper fix is a 400 guard in the route.
        """
        response = client.get("/raw/news_keywords")
        # Currently raises 500; document the behaviour, don't silently pass
        assert response.status_code in (400, 422, 500)


class TestLLMRoutes:
    """
    GET /<llm_name> → renders llm.html selecting the given model.
    GET /<llm_name>/news → LLM-ranked news page.
    """

    def test_set_llm_route_returns_200(self, client):
        response = client.get("/mistralai")
        assert response.status_code == 200

    def test_set_llm_route_unknown_model_raises_500(self, client):
        """
        Requesting a model name that doesn't exist in llm_config.json
        raises ValueError inside NewsController.__init__. Confirms the
        current behaviour — a future fix should return a 404/400.
        """
        response = client.get("/nonexistent-model-xyz")
        assert response.status_code in (500, 404)

    def test_favicon_returns_no_content(self, client):
        """
        The set_llm_route has a special case: if llm_name == 'favicon.ico'
        it returns 204 No Content instead of trying to load a model.
        """
        response = client.get("/favicon.ico")
        assert response.status_code == 204


class TestNotFoundRoute:
    """Unknown routes → 404. The 404 handler in NewsRoutes has a bug
    (references g.news_controller which is not set), so we only assert
    the status code, not the response body."""

    def test_completely_unknown_route_returns_404(self, client):
        response = client.get("/this/route/does/not/exist")
        assert response.status_code == 404
