import os
import sys
from unittest.mock import MagicMock, patch

import pytest


TEST_DIR = os.path.dirname(__file__)
INGESTION_DIR = os.path.abspath(os.path.join(TEST_DIR, ".."))
if INGESTION_DIR not in sys.path:
    sys.path.insert(0, INGESTION_DIR)

import embeddings
import handler
import poller


def test_normalize_url_strips_tracking_and_fragment():
    url = "HTTPS://Example.COM/path?a=1&utm_source=x&gclid=y#section"
    normalized = poller.normalize_url(url)
    assert normalized == "https://example.com/path?a=1"


def test_compute_url_hash_is_stable():
    normalized = "https://example.com/news"
    h1 = poller.compute_url_hash(normalized)
    h2 = poller.compute_url_hash(normalized)
    assert h1 == h2
    assert len(h1) == 64


def test_parse_entry_missing_required_fields_returns_none():
    feed = {"name": "Feed", "url": "https://feed.example"}
    entry = {"title": "", "link": ""}
    parsed = poller._parse_entry(entry, feed)
    assert parsed is None


def test_build_job_structure():
    payload = {
        "title": "T",
        "url": "https://example.com/a",
        "url_hash": "abc123",
        "content_snippet": "snippet",
        "author": "author",
        "source_name": "source",
        "feed_url": "https://feed.example",
        "image_url": None,
        "published_at": None,
    }
    job = poller._build_job(payload)
    assert job["event_type"] == "article.discovered"
    assert job["idempotency_key"] == "article:abc123:discovered"
    assert job["payload"]["url_hash"] == "abc123"


def test_prepare_embedding_text():
    text = embeddings.prepare_embedding_text("Title", "Snippet")
    assert text == "Title Snippet"


@patch("embeddings._get_model", side_effect=Exception("boom"))
def test_generate_embedding_failure_returns_empty_list(_mock_model):
    vector = embeddings.generate_embedding("hello")
    assert vector == []


def test_unknown_event_type_is_skipped():
    with patch("handler.get_connection") as mock_get_conn:
        handler.handle_article_discovered({"event_type": "other", "payload": {}, "idempotency_key": "k"})
        mock_get_conn.assert_not_called()


@pytest.fixture
def fake_conn_ctx():
    conn = MagicMock()

    class _Ctx:
        def __enter__(self_inner):
            return conn

        def __exit__(self_inner, exc_type, exc, tb):
            return False

    return conn, _Ctx()


@patch("handler.mark_processed")
@patch("handler.upsert_article", return_value=True)
@patch("handler.generate_embedding", return_value=[0.1, 0.2])
@patch("handler.prepare_embedding_text", return_value="text")
@patch("handler.is_processed", return_value=False)
def test_article_discovered_success_path(
    _mock_is_processed,
    _mock_prepare,
    _mock_generate,
    mock_upsert,
    mock_mark,
    fake_conn_ctx,
):
    conn, ctx = fake_conn_ctx
    event = {
        "event_type": "article.discovered",
        "idempotency_key": "article:hash:discovered",
        "payload": {
            "title": "Some title",
            "content_snippet": "Some snippet",
            "url": "https://example.com",
            "url_hash": "hash",
            "source_name": "src",
        },
    }

    with patch("handler.get_connection", return_value=ctx):
        handler.handle_article_discovered(event)

    mock_upsert.assert_called_once()
    mock_mark.assert_called_once_with(conn, "article:hash:discovered", "article.discovered")
    conn.commit.assert_called_once()


@patch("handler.mark_processed")
@patch("handler.upsert_article", return_value=False)
@patch("handler.generate_embedding", return_value=[])
@patch("handler.prepare_embedding_text", return_value="text")
@patch("handler.is_processed", return_value=False)
def test_article_discovered_embedding_failure_marks_failed(
    _mock_is_processed,
    _mock_prepare,
    _mock_generate,
    mock_upsert,
    mock_mark,
    fake_conn_ctx,
):
    _conn, ctx = fake_conn_ctx
    event = {
        "event_type": "article.discovered",
        "idempotency_key": "article:hash:discovered",
        "payload": {
            "title": "Some title",
            "content_snippet": "Some snippet",
            "url": "https://example.com",
            "url_hash": "hash",
            "source_name": "src",
        },
    }

    with patch("handler.get_connection", return_value=ctx):
        handler.handle_article_discovered(event)

    args, _kwargs = mock_upsert.call_args
    assert args[3] == "failed"
    mock_mark.assert_called_once()
