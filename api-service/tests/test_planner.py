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
        "active_article": None,
    }
    base.update(kwargs)
    return base


class TestPlannerAgentKeywordFallback:
    """LLM call mocked to return None (unavailable/failed) - tests the
    existing keyword-matching fallback path deterministically, regardless
    of whether HF_TOKEN happens to be set in the environment."""

    def test_search_intent(self, mocker):
        from agents import planner
        mocker.patch.object(planner, "classify_intent", return_value=None)
        state = make_state(user_input="show me latest ransomware news")
        result = planner.planner_agent(state)
        assert result["intent"] == "search"

    def test_analyze_intent(self, mocker):
        from agents import planner
        mocker.patch.object(planner, "classify_intent", return_value=None)
        state = make_state(user_input="analyze trends in malware attacks")
        result = planner.planner_agent(state)
        assert result["intent"] == "analyze"

    def test_subscribe_intent(self, mocker):
        from agents import planner
        mocker.patch.object(planner, "classify_intent", return_value=None)
        state = make_state(user_input="subscribe me to daily digest")
        result = planner.planner_agent(state)
        assert result["intent"] == "subscribe"

    def test_default_intent_is_search(self, mocker):
        from agents import planner
        mocker.patch.object(planner, "classify_intent", return_value=None)
        state = make_state(user_input="ransomware")
        result = planner.planner_agent(state)
        assert result["intent"] == "search"

    def test_stop_words_stripped_from_keywords(self, mocker):
        from agents import planner
        mocker.patch.object(planner, "classify_intent", return_value=None)
        state = make_state(user_input="show me the latest ransomware news")
        result = planner.planner_agent(state)
        assert "show" not in result["keywords"]
        assert "the" not in result["keywords"]
        assert "latest" not in result["keywords"]
        assert "ransomware" in result["keywords"]

    def test_keywords_extracted(self, mocker):
        from agents import planner
        mocker.patch.object(planner, "classify_intent", return_value=None)
        state = make_state(user_input="find ransomware attacks")
        result = planner.planner_agent(state)
        assert "ransomware" in result["keywords"]
        assert "attacks" in result["keywords"]

    def test_word_boundary_matching_not_substring(self, mocker):
        """'target' shouldn't match the 'get' keyword trigger via substring."""
        from agents import planner
        mocker.patch.object(planner, "classify_intent", return_value=None)
        state = make_state(user_input="target systems affected")
        result = planner.planner_agent(state)
        assert result["intent"] == "search"  # falls to default, not a false subscribe/analyze match

    def test_non_force_grounded_turn_never_stays_grounded(self, mocker):
        """Grounding is single-turn only - any turn that isn't the exact
        force_grounded turn always clears active_article, regardless of
        what the LLM (or its absence) returns."""
        from agents import planner
        mocker.patch.object(planner, "classify_intent", return_value=None)
        state = make_state(user_input="tell me more", active_article={"id": "1", "title": "t"})
        result = planner.planner_agent(state)
        assert result["active_article"] is None


class TestPlannerAgentLlmClassification:
    def test_llm_intent_used_when_available(self, mocker):
        from agents import planner
        mocker.patch.object(planner, "classify_intent", return_value={
            "intent": "chitchat", "keywords": [],
        })
        state = make_state(user_input="hi")
        result = planner.planner_agent(state)
        assert result["intent"] == "chitchat"


class TestPlannerAgentForceGrounded:
    def test_force_grounded_skips_llm_call_entirely(self, mocker):
        from agents import planner
        classify_spy = mocker.patch.object(planner, "classify_intent")
        article = {"id": "1", "title": "Critical RCE Found"}
        state = make_state(
            user_input="tell me about this article: Critical RCE Found",
            active_article=article,
            force_grounded=True,
        )
        result = planner.planner_agent(state)
        assert result["intent"] == "grounded"
        assert result["active_article"] == article
        classify_spy.assert_not_called()

    def test_force_grounded_without_active_article_falls_through_normally(self, mocker):
        from agents import planner
        mocker.patch.object(planner, "classify_intent", return_value=None)
        state = make_state(user_input="hello", active_article=None, force_grounded=True)
        result = planner.planner_agent(state)
        assert result["intent"] == "search"

    def test_not_force_grounded_still_asks_llm_normally(self, mocker):
        from agents import planner
        classify_spy = mocker.patch.object(planner, "classify_intent", return_value={
            "intent": "search", "keywords": ["phishing"],
        })
        article = {"id": "1", "title": "t"}
        state = make_state(user_input="find me phishing news", active_article=article, force_grounded=False)
        result = planner.planner_agent(state)
        assert result["intent"] == "search"
        assert result["active_article"] is None
        classify_spy.assert_called_once()
