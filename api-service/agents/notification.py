import re
import json
import hashlib
import os
import redis
from agents.state import PlannerState

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
DIGEST_QUEUE = "digest-jobs"

try:
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
except Exception:
    redis_client = None

def _extract_email(text: str) -> str:
    match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
    return match.group(0) if match else ""

def _extract_frequency(text: str) -> str:
    if "weekly" in text.lower():
        return "weekly"
    return "daily"

def notification_agent(state: PlannerState) -> PlannerState:
    user_input = state.get("user_input", "")
    keywords = state.get("keywords", [])

    email = _extract_email(user_input)
    frequency = _extract_frequency(user_input)
    # keywords from PlannerAgent become the subscriber's interest tags
    interests = [k for k in keywords if k not in {"subscribe", "notify", "alert", "digest", "to", "for", "me", "daily", "weekly"}]

    payload = {
        "email": email,
        "frequency": frequency,
        "interests": interests,
    }

    idempotency_key = "digest:" + hashlib.md5(
        f"{email}:{frequency}".encode()
    ).hexdigest()

    job = {
        "event_type": "article.digest",
        "idempotency_key": idempotency_key,
        "payload": payload,
    }

    if redis_client:
        try:
            redis_client.lpush(DIGEST_QUEUE, json.dumps(job))
        except Exception:
            pass

    return {**state, "notification_triggered": True}
