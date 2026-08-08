from agents.state import PlannerState
from services.chat_llm import classify_intent

INTENT_KEYWORDS = {
    "search": ["latest", "news", "what", "show", "find", "get"],
    "analyze": ["trend", "analyze", "sentiment", "frequency", "popular"],
    "subscribe": ["subscribe", "notify", "alert", "digest"],
}


def _keyword_fallback_intent(user_input: str) -> str:
    """Word-boundary keyword matching, used when the LLM call fails or is
    unavailable. Splits on whitespace rather than substring-matching the
    raw string, so "target" doesn't match "get" or "somewhat" match "what".
    """
    words = set(user_input.split())
    for detected_intent, triggers in INTENT_KEYWORDS.items():
        if words & set(triggers):
            return detected_intent
    return "search"


def planner_agent(state: PlannerState) -> PlannerState:
    raw_input = state["user_input"]
    user_input = raw_input.lower()
    active_article = state.get("active_article")

    # force_grounded is set by the route for the exact turn the user clicked
    # "Ask AI" on a specific article. Grounding only ever applies to this
    # one turn - the reply includes a real link back to the article instead
    # of trying to track whether follow-up messages are still on-topic,
    # since that judgment call proved unreliable across multiple attempts.
    if state.get("force_grounded") and active_article:
        return {**state, "intent": "grounded", "keywords": [], "active_article": active_article}

    classified = classify_intent(raw_input)

    if classified:
        intent = classified["intent"]
        keywords = classified["keywords"]
    else:
        intent = _keyword_fallback_intent(user_input)
        stop_words = {"the", "a", "an", "is", "are", "what", "show", "me", "find", "get", "latest"}
        keywords = [w for w in user_input.split() if w not in stop_words]

    return {**state, "intent": intent, "keywords": keywords, "active_article": None}
