import json
import hashlib
import os
import redis
from agents.state import PlannerState

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CACHE_TTL = 300  # 5 minutes

try:
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
except Exception:
    redis_client = None

def _cache_key(user_input: str, intent: str) -> str:
    raw = f"{intent}:{user_input.strip().lower()}"
    return "chat:" + hashlib.md5(raw.encode()).hexdigest()

def responder_agent(state: PlannerState) -> PlannerState:
    articles = state.get("retrieved_articles", [])
    analysis = state.get("analysis", None)
    user_input = state.get("user_input", "")
    intent = state.get("intent", "search")

    if intent == "subscribe":
        response = {"message": "Subscribed successfully. You will receive digests based on your interests.", "articles": []}
        return {**state, "llm_response": json.dumps(response)}

    cache_key = _cache_key(user_input, intent)

    if redis_client:
        try:
            cached = redis_client.get(cache_key)
            if cached:
                return {**state, "llm_response": cached}
        except Exception:
            pass

    if not articles:
        response = {"message": "No articles found for your query.", "articles": []}
    else:
        response = {
            "message": f"Found {len(articles)} articles.",
            "articles": articles,
            "analysis": analysis,
        }

    result = json.dumps(response)

    if redis_client:
        try:
            redis_client.setex(cache_key, CACHE_TTL, result)
        except Exception:
            pass

    return {**state, "llm_response": result}
