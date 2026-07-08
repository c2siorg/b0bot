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
