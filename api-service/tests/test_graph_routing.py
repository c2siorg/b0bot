import pytest
from unittest.mock import MagicMock


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
