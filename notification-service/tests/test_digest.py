import os
import sys
from datetime import datetime, timedelta, timezone
from unittest.mock import patch


TEST_DIR = os.path.dirname(__file__)
SERVICE_DIR = os.path.abspath(os.path.join(TEST_DIR, ".."))
if SERVICE_DIR not in sys.path:
    sys.path.insert(0, SERVICE_DIR)

from digest import get_window_start, make_idempotency_key, render_digest_email, select_articles_for_digest


def test_get_window_start_daily():
    now = datetime(2026, 6, 30, 12, 0, 0, tzinfo=timezone.utc)
    start = get_window_start(now, "daily")
    assert start == now - timedelta(days=1)


def test_get_window_start_weekly():
    now = datetime(2026, 6, 30, 12, 0, 0, tzinfo=timezone.utc)
    start = get_window_start(now, "weekly")
    assert start == now - timedelta(days=7)


def test_make_idempotency_key():
    window_start = datetime(2026, 6, 29, 12, 0, 0, tzinfo=timezone.utc)
    key = make_idempotency_key("sub-1", "daily", window_start)
    assert key == "digest:sub-1:daily:2026-06-29T12:00:00+00:00"


def test_select_articles_for_digest_latest_slice_only():
    articles = [{"id": i} for i in range(20)]
    selected = select_articles_for_digest(articles, limit=10)
    assert len(selected) == 10
    assert selected[0]["id"] == 0


def test_render_digest_email_with_articles():
    with patch.dict("os.environ", {"FRONTEND_URL": "https://b0bot.example"}, clear=False):
        # Re-import to pick up patched env-backed frontend URL.
        import importlib
        import digest as digest_module

        importlib.reload(digest_module)

    subject, body, html_body = digest_module.render_digest_email(
        [
            {
                "title": "Critical advisory",
                "source_name": "SecurityWeek",
                "url": "https://example.com/advisory",
            }
        ],
        "daily",
    )
    assert subject == "B0Bot daily digest"
    assert "Critical advisory" in body
    assert "https://b0bot.example/news?url=https%3A%2F%2Fexample.com%2Fadvisory" in body
    assert "Critical advisory" in html_body
    assert "Browse all news" in html_body


def test_render_digest_email_empty():
    subject, body, html_body = render_digest_email([], "weekly")
    assert subject == "B0Bot weekly digest"
    assert "No new articles were published" in body
    assert "Browse all news" in html_body


def test_render_digest_email_missing_article_fields_uses_defaults():
    subject, body, html_body = render_digest_email([{}], "daily")

    assert subject == "B0Bot daily digest"
    assert "Untitled" in body
    assert "Unknown Source" in body
    assert "Untitled" in html_body
    assert "Unknown source" in html_body
    assert "Browse all news" in html_body


def test_render_digest_email_missing_url_falls_back_to_frontend():
    with patch.dict("os.environ", {"FRONTEND_URL": "https://b0bot.example"}, clear=False):
        import importlib
        import digest as digest_module

        importlib.reload(digest_module)

    _subject, body, html_body = digest_module.render_digest_email(
        [{"title": "No link article", "source_name": "Feed"}],
        "daily",
    )

    assert "https://b0bot.example" in body
    assert "https://b0bot.example" in html_body
    assert "news?url=" not in body
