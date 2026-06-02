import json
from agents.state import PlannerState

def responder_agent(state: PlannerState) -> PlannerState:
    articles = state.get("retrieved_articles", [])
    chat_history = state.get("chat_history", [])

    if not articles:
        response = {"message": "No articles found for your query.", "articles": []}
    else:
        response = {
            "message": f"Found {len(articles)} articles.",
            "articles": articles,
            "chat_history": chat_history,
        }

    return {**state, "llm_response": json.dumps(response)}
