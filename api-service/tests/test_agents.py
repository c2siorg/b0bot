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
        "date": "01/06/2025",
        "url": "https://example.com/1",
        "body": "A ransomware attack encrypted patient records.",
    },
    {
        "title": "Apache patch released",
        "source": "The Hacker News",
        "date": "02/06/2025",
        "url": "https://example.com/2",
        "body": "Apache released a patch fixing a critical RCE vulnerability.",
    },
]



class TestPlannerAgent:
    def test_search_intent(self):
        from agents.planner import planner_agent
        state = make_state(user_input="show me latest ransomware news")
        result = planner_agent(state)
        assert result["intent"] == "search"

    def test_analyze_intent(self):
        from agents.planner import planner_agent
        state = make_state(user_input="analyze trends in malware attacks")
        result = planner_agent(state)
        assert result["intent"] == "analyze"

    def test_subscribe_intent(self):
        from agents.planner import planner_agent
        state = make_state(user_input="subscribe me to daily digest")
        result = planner_agent(state)
        assert result["intent"] == "subscribe"

    def test_default_intent_is_search(self):
        from agents.planner import planner_agent
        state = make_state(user_input="ransomware")
        result = planner_agent(state)
        assert result["intent"] == "search"

    def test_stop_words_stripped_from_keywords(self):
        from agents.planner import planner_agent
        state = make_state(user_input="show me the latest ransomware news")
        result = planner_agent(state)
        assert "show" not in result["keywords"]
        assert "the" not in result["keywords"]
        assert "latest" not in result["keywords"]
        assert "ransomware" in result["keywords"]

    def test_keywords_extracted(self):
        from agents.planner import planner_agent
        state = make_state(user_input="find ransomware attacks")
        result = planner_agent(state)
        assert "ransomware" in result["keywords"]
        assert "attacks" in result["keywords"]



class TestScraperAgent:
    def test_keyword_search_called_with_meaningful_keywords(self, mocker):
        from agents import scraper as scraper_module
        mock_db = MagicMock()
        mock_db.get_news_collections.return_value = [{"headlines": "t", "author": "x", "newsDate": "01/01/2025", "newsURL": "http://x.com", "fullNews": ""}]
        mocker.patch.object(scraper_module, "db", mock_db)

        from agents.scraper import scraper_agent
        state = make_state(intent="search", keywords=["ransomware", "attack"])
        scraper_agent(state)

        mock_db.get_news_collections.assert_called_once_with(
            is_keyword=True, keyword="ransomware attack"
        )

    def test_generic_terms_filtered_out(self, mocker):
        from agents import scraper as scraper_module
        mock_db = MagicMock()
        mock_db.get_news_collections.return_value = [{"headlines": "t", "author": "x", "newsDate": "01/01/2025", "newsURL": "http://x.com", "fullNews": ""}]
        mocker.patch.object(scraper_module, "db", mock_db)

        from agents.scraper import scraper_agent
        state = make_state(intent="search", keywords=["cybersecurity", "news", "ransomware"])
        scraper_agent(state)

        mock_db.get_news_collections.assert_called_once_with(
            is_keyword=True, keyword="ransomware"
        )

    def test_falls_back_when_all_keywords_are_generic(self, mocker):
        from agents import scraper as scraper_module
        mock_db = MagicMock()
        mock_db.get_news_collections.return_value = []
        mocker.patch.object(scraper_module, "db", mock_db)

        from agents.scraper import scraper_agent
        state = make_state(intent="search", keywords=["cybersecurity", "news"])
        scraper_agent(state)

        mock_db.get_news_collections.assert_called_once_with()

    def test_falls_back_when_keyword_search_returns_empty(self, mocker):
        from agents import scraper as scraper_module
        mock_db = MagicMock()
        mock_db.get_news_collections.side_effect = [[], [{"headlines": "test", "author": "x", "newsDate": "01/01/2025", "newsURL": "http://x.com", "fullNews": ""}]]
        mocker.patch.object(scraper_module, "db", mock_db)

        from agents.scraper import scraper_agent
        state = make_state(intent="search", keywords=["ransomware"])
        scraper_agent(state)

        assert mock_db.get_news_collections.call_count == 2

    def test_articles_normalized_correctly(self, mocker):
        from agents import scraper as scraper_module
        raw = [{"headlines": "Test", "author": "Src", "newsDate": "01/01/2025", "newsURL": "http://x.com", "fullNews": "body text"}]
        mock_db = MagicMock()
        mock_db.get_news_collections.return_value = raw
        mocker.patch.object(scraper_module, "db", mock_db)

        from agents.scraper import scraper_agent
        state = make_state(intent="search", keywords=["ransomware"])
        result = scraper_agent(state)

        assert result["retrieved_articles"][0] == {
            "title": "Test",
            "source": "Src",
            "date": "01/01/2025",
            "url": "http://x.com",
            "body": "body text",
        }



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



class TestNotificationAgent:
    def test_email_extracted(self, mocker):
        from agents import notification as notification_module
        mock_redis = MagicMock()
        mocker.patch.object(notification_module, "redis_client", mock_redis)

        from agents.notification import notification_agent
        state = make_state(user_input="subscribe vishak@example.com daily", keywords=["vishak@example.com", "daily"])
        result = notification_agent(state)

        job = json.loads(mock_redis.lpush.call_args[0][1])
        assert job["payload"]["email"] == "vishak@example.com"

    def test_weekly_frequency_extracted(self, mocker):
        from agents import notification as notification_module
        mock_redis = MagicMock()
        mocker.patch.object(notification_module, "redis_client", mock_redis)

        from agents.notification import notification_agent
        state = make_state(user_input="subscribe vishak@example.com weekly", keywords=[])
        result = notification_agent(state)

        job = json.loads(mock_redis.lpush.call_args[0][1])
        assert job["payload"]["frequency"] == "weekly"

    def test_default_frequency_is_daily(self, mocker):
        from agents import notification as notification_module
        mock_redis = MagicMock()
        mocker.patch.object(notification_module, "redis_client", mock_redis)

        from agents.notification import notification_agent
        state = make_state(user_input="subscribe vishak@example.com", keywords=[])
        result = notification_agent(state)

        job = json.loads(mock_redis.lpush.call_args[0][1])
        assert job["payload"]["frequency"] == "daily"

    def test_job_pushed_to_digest_queue(self, mocker):
        from agents import notification as notification_module
        mock_redis = MagicMock()
        mocker.patch.object(notification_module, "redis_client", mock_redis)

        from agents.notification import notification_agent
        state = make_state(user_input="subscribe vishak@example.com", keywords=[])
        notification_agent(state)

        assert mock_redis.lpush.call_args[0][0] == "digest-jobs"

    def test_notification_triggered_set_true(self, mocker):
        from agents import notification as notification_module
        mock_redis = MagicMock()
        mocker.patch.object(notification_module, "redis_client", mock_redis)

        from agents.notification import notification_agent
        state = make_state(user_input="subscribe vishak@example.com", keywords=[])
        result = notification_agent(state)

        assert result["notification_triggered"] is True



class TestGraphRouting:
    def test_search_intent_routes_through_scraper(self, mocker):
        from agents import scraper as scraper_module
        from agents import responder as responder_module
        mock_db = MagicMock()
        mock_db.get_news_collections.return_value = []
        mocker.patch.object(scraper_module, "db", mock_db)
        mock_redis = MagicMock()
        mock_redis.get.return_value = None
        mocker.patch.object(responder_module, "redis_client", mock_redis)

        from agents import agent_graph
        result = agent_graph.invoke({
            "user_input": "show me ransomware news",
            "session_id": "test",
            "chat_history": [],
            "notification_triggered": False,
        })

        assert result["intent"] == "search"
        assert result["llm_response"] is not None
        mock_db.get_news_collections.assert_called()

    def test_subscribe_intent_skips_scraper(self, mocker):
        from agents import scraper as scraper_module
        from agents import notification as notification_module
        from agents import responder as responder_module
        mock_db = MagicMock()
        mocker.patch.object(scraper_module, "db", mock_db)
        mock_redis = MagicMock()
        mocker.patch.object(notification_module, "redis_client", mock_redis)
        mocker.patch.object(responder_module, "redis_client", mock_redis)

        from agents import agent_graph
        result = agent_graph.invoke({
            "user_input": "subscribe vishak@example.com daily",
            "session_id": "test",
            "chat_history": [],
            "notification_triggered": False,
        })

        assert result["intent"] == "subscribe"
        assert result["notification_triggered"] is True
        mock_db.get_news_collections.assert_not_called()
