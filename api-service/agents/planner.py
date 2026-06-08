from agents.state import PlannerState

INTENT_KEYWORDS = {
    "search": ["latest", "news", "what", "show", "find", "get"],
    "analyze": ["trend", "analyze", "sentiment", "frequency", "popular"],
    "subscribe": ["subscribe", "notify", "alert", "digest"],
}

def planner_agent(state: PlannerState) -> PlannerState:
    user_input = state["user_input"].lower()

    intent = "search"  # default
    for detected_intent, triggers in INTENT_KEYWORDS.items():
        if any(word in user_input for word in triggers):
            intent = detected_intent
            break

    # Basic keyword extraction — strip common stop words
    stop_words = {"the", "a", "an", "is", "are", "what", "show", "me", "find", "get", "latest"}
    keywords = [w for w in user_input.split() if w not in stop_words]

    return {**state, "intent": intent, "keywords": keywords}
