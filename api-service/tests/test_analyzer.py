import pytest
from unittest.mock import MagicMock


def make_state(**kwargs):
    base = {
        "user_input": "",
        "intent": None,
        "keywords": [],
        "retrieved_articles": [],
        "llm_response": None,
        "session_id": "test-session",
        "chat_history": [],
        "notification_triggered": False,
        "analysis": None,
    }
    base.update(kwargs)
    return base


SAMPLE_ARTICLES = [
    {
        "title": "Ransomware hits hospital",
        "source": "BleepingComputer",
        "date": "01/01/2026",
        "url": "https://example.com/1",
        "body": "A ransomware attack encrypted patient records.",
    },
    {
        "title": "Apache patch released",
        "source": "The Hacker News",
        "date": "01/01/2026",
        "url": "https://example.com/2",
        "body": "Apache released a patch fixing a critical RCE vulnerability.",
    },
]


class TestAnalyzerAgent:
    def test_returns_none_analysis_when_no_articles(self):
        from agents.analyzer import analyzer_agent
        state = make_state(retrieved_articles=[])
        result = analyzer_agent(state)
        assert result["analysis"] is None

    def test_analysis_keys_present(self):
        from agents.analyzer import analyzer_agent
        state = make_state(retrieved_articles=SAMPLE_ARTICLES)
        result = analyzer_agent(state)
        assert "keyword_frequency" in result["analysis"]
        assert "trending_topics" in result["analysis"]
        assert "sentiment" in result["analysis"]
        assert "positive_signals" in result["analysis"]
        assert "negative_signals" in result["analysis"]

    # sentiment logic is keyword-based for now; these tests will be updated when DistilBERT lands
    def test_negative_sentiment(self):
        from agents.analyzer import analyzer_agent
        articles = [{"title": "ransomware vulnerability exploit breach", "body": "malware attack compromised exposed leaked"}]
        state = make_state(retrieved_articles=articles)
        result = analyzer_agent(state)
        assert result["analysis"]["sentiment"] == "negative"

    def test_positive_sentiment(self):
        from agents.analyzer import analyzer_agent
        articles = [{"title": "patched fixed resolved mitigated secured", "body": "updated protected systems"}]
        state = make_state(retrieved_articles=articles)
        result = analyzer_agent(state)
        assert result["analysis"]["sentiment"] == "positive"

    def test_neutral_sentiment_when_equal_signals(self):
        from agents.analyzer import analyzer_agent
        articles = [{"title": "ransomware patched", "body": "vulnerability fixed"}]
        state = make_state(retrieved_articles=articles)
        result = analyzer_agent(state)
        assert result["analysis"]["sentiment"] == "neutral"
