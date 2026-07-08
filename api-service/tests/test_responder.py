import json
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


class TestResponderAgent:
    def test_subscribe_intent_bypasses_cache(self, mocker):
        from agents import responder as responder_module
        mock_redis = MagicMock()
        mocker.patch.object(responder_module, "redis_client", mock_redis)
        from agents.responder import responder_agent
        state = make_state(intent="subscribe", user_input="subscribe me")
        result = responder_agent(state)
        mock_redis.get.assert_not_called()
        response = json.loads(result["llm_response"])
        assert "Subscribed" in response["message"]

    def test_cache_hit_returns_cached_value(self, mocker):
        from agents import responder as responder_module
        mock_redis = MagicMock()
        cached = json.dumps({"message": "cached response", "articles": []})
        mock_redis.get.return_value = cached
        mocker.patch.object(responder_module, "redis_client", mock_redis)
        from agents.responder import responder_agent
        state = make_state(intent="search", user_input="ransomware news", retrieved_articles=SAMPLE_ARTICLES)
        result = responder_agent(state)
        assert result["llm_response"] == cached
        mock_redis.setex.assert_not_called()

    def test_cache_miss_writes_to_cache(self, mocker):
        from agents import responder as responder_module
        mock_redis = MagicMock()
        mock_redis.get.return_value = None
        mocker.patch.object(responder_module, "redis_client", mock_redis)
        from agents.responder import responder_agent
        state = make_state(intent="search", user_input="ransomware news", retrieved_articles=SAMPLE_ARTICLES)
        result = responder_agent(state)
        mock_redis.setex.assert_called_once()
        response = json.loads(result["llm_response"])
        assert response["articles"] == SAMPLE_ARTICLES

    def test_no_articles_returns_not_found_message(self, mocker):
        from agents import responder as responder_module
        mock_redis = MagicMock()
        mock_redis.get.return_value = None
        mocker.patch.object(responder_module, "redis_client", mock_redis)
        from agents.responder import responder_agent
        state = make_state(intent="search", user_input="something obscure", retrieved_articles=[])
        result = responder_agent(state)
        response = json.loads(result["llm_response"])
        assert response["message"] == "No articles found for your query."

    def test_redis_down_does_not_crash(self, mocker):
        from agents import responder as responder_module
        mocker.patch.object(responder_module, "redis_client", None)
        from agents.responder import responder_agent
        state = make_state(intent="search", user_input="ransomware", retrieved_articles=SAMPLE_ARTICLES)
        result = responder_agent(state)
        assert result["llm_response"] is not None
