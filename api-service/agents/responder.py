import json
import hashlib
import os
import redis
from agents.state import PlannerState
from services.chat_llm import answer_grounded

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CACHE_TTL = 300  # 5 minutes
try:
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
except Exception:
    redis_client = None


def _cache_key(raw: str) -> str:
    return "chat:" + hashlib.md5(raw.encode()).hexdigest()


def _chitchat_reply(user_input: str) -> str:
    """Lightweight templated reply for small talk - no LLM call needed for
    a greeting or thanks, keeps latency low for the common case."""
    lowered = user_input.lower()
    if any(w in lowered for w in ("thank", "thanks")):
        return "you're welcome! let me know if you want to look into anything else."
    if any(w in lowered for w in ("bye", "goodbye")):
        return "see you around!"
    return "hey! ask me about cybersecurity news, or click ask AI on any article to dig into it."


def responder_agent(state: PlannerState) -> PlannerState:
    articles = state.get("retrieved_articles", [])
    analysis = state.get("analysis", None)
    user_input = state.get("user_input", "")
    intent = state.get("intent", "search")
    active_article = state.get("active_article")

    if intent == "subscribe":
        message = state.get("notification_message") or "Subscribed successfully."
        response = {"message": message, "articles": []}
        return {**state, "llm_response": json.dumps(response)}

    if intent == "chitchat":
        response = {"message": _chitchat_reply(user_input), "articles": []}
        return {**state, "llm_response": json.dumps(response)}

    if intent == "grounded" and active_article:
        # cache key includes the article id, not just the question text -
        # "tell me more" means something different per article, caching on
        # question text alone would leak article A's cached answer to article B
        cache_key = _cache_key(f"grounded:{active_article.get('id')}:{user_input.strip().lower()}")
        if redis_client:
            try:
                cached = redis_client.get(cache_key)
                if cached:
                    return {**state, "llm_response": cached}
            except Exception:
                pass
        answer = answer_grounded(active_article, user_input)
        if answer:
            message = answer + "\n\nWant to know more? Click the article below to read the full story."
        else:
            message = "I couldn't generate an answer for that, try rephrasing your question."
        # include the real article as a clickable card - same shape
        # ScraperAgent normalizes to - so the reply gives an actual link
        # to read more, instead of trying to guess whether a follow-up
        # question is still about this article.
        article_card = {
            "title": active_article.get("title", "No title"),
            "source": active_article.get("source_name", "No source"),
            "date": active_article.get("published_at", "") or "",
            "url": active_article.get("url", ""),
            "body": "",
            "summary": active_article.get("summary"),
        }
        response = {"message": message, "articles": [article_card]}
        result = json.dumps(response)
        if redis_client:
            try:
                redis_client.setex(cache_key, CACHE_TTL, result)
            except Exception:
                pass
        return {**state, "llm_response": result}

    cache_key = _cache_key(f"{intent}:{user_input.strip().lower()}")
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
            "message": f"Found {len(articles)} articles. Click any of them below to read the full story.",
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
