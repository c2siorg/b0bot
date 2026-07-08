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


class TestNotificationAgent:
    def test_email_extracted(self, mocker):
        from agents import notification as notification_module
        mock_redis = MagicMock()
        mocker.patch.object(notification_module, "redis_client", mock_redis)
        from agents.notification import notification_agent
        state = make_state(user_input="subscribe vishak@example.com daily", keywords=["vishak@example.com", "daily"])
        notification_agent(state)
        job = json.loads(mock_redis.lpush.call_args[0][1])
        assert job["payload"]["email"] == "vishak@example.com"

    def test_weekly_frequency_extracted(self, mocker):
        from agents import notification as notification_module
        mock_redis = MagicMock()
        mocker.patch.object(notification_module, "redis_client", mock_redis)
        from agents.notification import notification_agent
        state = make_state(user_input="subscribe vishak@example.com weekly", keywords=[])
        notification_agent(state)
        job = json.loads(mock_redis.lpush.call_args[0][1])
        assert job["payload"]["frequency"] == "weekly"

    def test_default_frequency_is_daily(self, mocker):
        from agents import notification as notification_module
        mock_redis = MagicMock()
        mocker.patch.object(notification_module, "redis_client", mock_redis)
        from agents.notification import notification_agent
        state = make_state(user_input="subscribe vishak@example.com", keywords=[])
        notification_agent(state)
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
