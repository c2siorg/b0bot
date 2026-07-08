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
        "title": "New malware strain bypasses antivirus detection",
        "source": "The Hacker News",
        "date": "01/01/2026",
        "url": "https://example.com/2",
        "body": "A new malware strain is actively exploiting vulnerabilities in enterprise systems.",
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
        assert "sentiment_confidence" in result["analysis"]
        assert "article_sentiments" in result["analysis"]

    def test_article_sentiments_per_article(self):
        from agents.analyzer import analyzer_agent
        state = make_state(retrieved_articles=SAMPLE_ARTICLES)
        result = analyzer_agent(state)
        assert len(result["analysis"]["article_sentiments"]) == 2
        for item in result["analysis"]["article_sentiments"]:
            assert "title" in item
            assert "sentiment" in item
            assert "confidence" in item
            assert item["sentiment"] in ("positive", "negative", "neutral")

    def test_negative_sentiment_on_ransomware(self):
        from agents.analyzer import analyzer_agent
        articles = [{"title": "ransomware campaign targets healthcare providers encrypting patient records", "body": "hospitals hit by ransomware attack demanding payment"}]
        state = make_state(retrieved_articles=articles)
        result = analyzer_agent(state)
        assert result["analysis"]["sentiment"] == "negative"

    def test_pipeline_none_falls_back_to_neutral(self, mocker):
        import agents.analyzer as analyzer_module
        mocker.patch.object(analyzer_module, "sentiment_pipeline", None)
        from agents.analyzer import analyzer_agent
        state = make_state(retrieved_articles=SAMPLE_ARTICLES)
        result = analyzer_agent(state)
        assert result["analysis"]["sentiment"] == "neutral"
