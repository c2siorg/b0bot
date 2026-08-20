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


class TestResponderAgentChitchat:
    def test_chitchat_returns_templated_reply_no_llm_call(self, mocker):
        from agents import responder as responder_module
        mock_redis = MagicMock()
        mock_redis.get.return_value = None
        mocker.patch.object(responder_module, "redis_client", mock_redis)
        answer_grounded_spy = mocker.patch.object(responder_module, "answer_grounded")
        from agents.responder import responder_agent
        state = make_state(user_input="hi", intent="chitchat")
        result = responder_agent(state)
        response = json.loads(result["llm_response"])
        assert response["articles"] == []
        assert "message" in response
        answer_grounded_spy.assert_not_called()

    def test_thanks_gets_thanks_reply(self, mocker):
        from agents import responder as responder_module
        mock_redis = MagicMock()
        mock_redis.get.return_value = None
        mocker.patch.object(responder_module, "redis_client", mock_redis)
        from agents.responder import responder_agent
        state = make_state(user_input="thanks!", intent="chitchat")
        result = responder_agent(state)
        response = json.loads(result["llm_response"])
        assert "welcome" in response["message"].lower()


class TestResponderAgentGrounded:
    def test_grounded_calls_answer_grounded_with_active_article(self, mocker):
        from agents import responder as responder_module
        mock_redis = MagicMock()
        mock_redis.get.return_value = None
        mocker.patch.object(responder_module, "redis_client", mock_redis)
        mocker.patch.object(responder_module, "answer_grounded", return_value="the RCE affects Apache servers")
        from agents.responder import responder_agent
        article = {"id": "1", "title": "Critical RCE Found", "summary": "s", "source_name": "Krebs"}
        state = make_state(user_input="what's affected?", intent="grounded", active_article=article)
        result = responder_agent(state)
        response = json.loads(result["llm_response"])
        assert response["message"] == "the RCE affects Apache servers\n\nWant to know more? Click the article below to read the full story."
        responder_module.answer_grounded.assert_called_once_with(article, "what's affected?")

    def test_grounded_response_includes_real_article_card(self, mocker):
        """The grounded reply includes an actual clickable link to the
        article, in the same shape ScraperAgent normalizes articles to, so
        the existing frontend rendering picks it up with no new JS needed."""
        from agents import responder as responder_module
        mock_redis = MagicMock()
        mock_redis.get.return_value = None
        mocker.patch.object(responder_module, "redis_client", mock_redis)
        mocker.patch.object(responder_module, "answer_grounded", return_value="an answer")
        from agents.responder import responder_agent
        article = {
            "id": "1", "title": "Critical RCE Found", "summary": "a summary",
            "source_name": "Krebs", "url": "https://example.com/rce",
        }
        state = make_state(user_input="what happened?", intent="grounded", active_article=article)
        result = responder_agent(state)
        response = json.loads(result["llm_response"])
        assert len(response["articles"]) == 1
        card = response["articles"][0]
        assert card["title"] == "Critical RCE Found"
        assert card["url"] == "https://example.com/rce"
        assert card["source"] == "Krebs"
        assert card["summary"] == "a summary"

    def test_grounded_answer_failure_returns_fallback_message(self, mocker):
        from agents import responder as responder_module
        mock_redis = MagicMock()
        mock_redis.get.return_value = None
        mocker.patch.object(responder_module, "redis_client", mock_redis)
        mocker.patch.object(responder_module, "answer_grounded", return_value=None)
        from agents.responder import responder_agent
        article = {"id": "1", "title": "t"}
        state = make_state(user_input="what's affected?", intent="grounded", active_article=article)
        result = responder_agent(state)
        response = json.loads(result["llm_response"])
        assert "couldn't" in response["message"].lower()

    def test_grounded_cache_key_includes_article_id(self, mocker):
        """Same question text, different articles, must not share a cache
        entry - caching on question text alone would leak article A's
        cached answer to article B."""
        from agents import responder as responder_module
        mock_redis = MagicMock()
        mock_redis.get.return_value = None
        mocker.patch.object(responder_module, "redis_client", mock_redis)
        mocker.patch.object(responder_module, "answer_grounded", return_value="an answer")
        from agents.responder import responder_agent
        state_a = make_state(user_input="tell me more", intent="grounded", active_article={"id": "article-a", "title": "t"})
        state_b = make_state(user_input="tell me more", intent="grounded", active_article={"id": "article-b", "title": "t"})
        responder_agent(state_a)
        responder_agent(state_b)
        cache_keys_used = [call.args[0] for call in mock_redis.get.call_args_list]
        assert cache_keys_used[0] != cache_keys_used[1]
