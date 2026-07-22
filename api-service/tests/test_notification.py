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
        "notification_message": None,
        "analysis": None,
    }
    base.update(kwargs)
    return base


class TestNotificationAgent:
    def test_asks_for_email_when_missing(self, mocker):
        from agents.notification import notification_agent
        state = make_state(user_input="subscribe me to malware alerts daily")
        result = notification_agent(state)
        assert result["notification_triggered"] is False
        assert "email" in result["notification_message"].lower()

    def test_asks_for_interests_when_no_known_tag_matched(self, mocker):
        from agents.notification import notification_agent
        state = make_state(user_input="subscribe vishak@example.com to cybersecurity news")
        result = notification_agent(state)
        assert result["notification_triggered"] is False
        assert "topics" in result["notification_message"].lower()

    def test_everything_is_a_valid_choice(self, mocker):
        from agents import notification as notification_module
        mock_db = MagicMock()
        mock_db.create_subscriber.return_value = True
        mocker.patch.object(notification_module, "db", mock_db)
        from agents.notification import notification_agent
        state = make_state(user_input="subscribe vishak@example.com to everything daily")
        result = notification_agent(state)
        assert result["notification_triggered"] is True
        mock_db.create_subscriber.assert_called_once_with(email="vishak@example.com", frequency="daily", interests=[])

    def test_known_interest_matched(self, mocker):
        from agents import notification as notification_module
        mock_db = MagicMock()
        mock_db.create_subscriber.return_value = True
        mocker.patch.object(notification_module, "db", mock_db)
        from agents.notification import notification_agent
        state = make_state(user_input="subscribe vishak@example.com to ransomware alerts weekly")
        result = notification_agent(state)
        assert result["notification_triggered"] is True
        mock_db.create_subscriber.assert_called_once_with(email="vishak@example.com", frequency="weekly", interests=["ransomware"])

    def test_default_frequency_is_daily(self, mocker):
        from agents import notification as notification_module
        mock_db = MagicMock()
        mock_db.create_subscriber.return_value = True
        mocker.patch.object(notification_module, "db", mock_db)
        from agents.notification import notification_agent
        state = make_state(user_input="subscribe vishak@example.com to malware")
        result = notification_agent(state)
        mock_db.create_subscriber.assert_called_once_with(email="vishak@example.com", frequency="daily", interests=["malware"])

    def test_multi_turn_gathers_email_from_prior_subscribe_turn(self, mocker):
        from agents import notification as notification_module
        mock_db = MagicMock()
        mock_db.create_subscriber.return_value = True
        mocker.patch.object(notification_module, "db", mock_db)
        from agents.notification import notification_agent
        history = [
            {"role": "user", "content": "subscribe me daily", "intent": "subscribe"},
            {"role": "assistant", "content": "what email should I use?"},
        ]
        state = make_state(user_input="vishak@example.com, ransomware please", chat_history=history)
        result = notification_agent(state)
        assert result["notification_triggered"] is True
        mock_db.create_subscriber.assert_called_once_with(email="vishak@example.com", frequency="daily", interests=["ransomware"])

    def test_unrelated_prior_turn_not_included(self, mocker):
        from agents.notification import notification_agent
        history = [
            {"role": "user", "content": "show me ransomware news", "intent": "search"},
            {"role": "assistant", "content": "here are some articles"},
        ]
        state = make_state(user_input="subscribe me daily", chat_history=history)
        result = notification_agent(state)
        assert result["notification_triggered"] is False
        assert "email" in result["notification_message"].lower()
