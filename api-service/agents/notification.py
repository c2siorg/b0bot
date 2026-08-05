import re
from agents.state import PlannerState
from models.SubscriberModel import SubscriberDB

KNOWN_INTEREST_TAGS = {
    "malware", "ransomware", "cve", "data breach", "vulnerability",
    "phishing", "zero-day", "data leak", "supply chain", "insider threat",
}
EVERYTHING_PHRASES = {"everything", "all articles", "all news", "anything", "all topics"}

db = SubscriberDB()


def _extract_email(text: str) -> str:
    match = re.search(r"(?<![\w.])[a-zA-Z0-9_%+-]+(?:\.[a-zA-Z0-9_%+-]+)*@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*\.[a-zA-Z]{2,}(?![\w.])", text)
    return match.group(0) if match else ""


UNSUPPORTED_FREQUENCY_TERMS = {"hourly", "monthly", "biweekly", "quarterly", "real-time", "instant", "every hour", "every 12 hours"}


def _extract_frequency(text: str) -> str | None:
    lowered = text.lower()
    if "weekly" in lowered:
        return "weekly"
    if any(term in lowered for term in UNSUPPORTED_FREQUENCY_TERMS):
        return None
    return "daily"


def _extract_known_interests(text: str) -> list[str]:
    lowered = text.lower()
    return [tag for tag in sorted(KNOWN_INTEREST_TAGS) if tag in lowered]


def _wants_everything(text: str) -> bool:
    lowered = text.lower()
    return any(phrase in lowered for phrase in EVERYTHING_PHRASES)


def _gather_subscribe_context(state: PlannerState) -> str:
    """Combine the current message with any prior turns that were also
    part of this subscribe flow, so a multi-turn clarification (email in
    one message, topics in the next) still has full context. Stops at the
    first prior turn that wasn't subscribe intent, so unrelated earlier
    messages never leak into this.
    """
    history = state.get("chat_history") or []
    parts = []
    for entry in reversed(history):
        if entry.get("role") != "user":
            continue
        if entry.get("intent") != "subscribe":
            break
        parts.append(entry.get("content", ""))
    parts.reverse()
    parts.append(state.get("user_input", ""))
    return " ".join(parts)


def notification_agent(state: PlannerState) -> PlannerState:
    combined = _gather_subscribe_context(state)

    email = _extract_email(combined)
    if not email:
        return {
            **state,
            "notification_triggered": False,
            "notification_message": "what email should I use for the subscription?",
        }

    frequency = _extract_frequency(combined)
    if frequency is None:
        return {
            **state,
            "notification_triggered": False,
            "notification_message": "only daily or weekly digests are supported right now, which one do you want?",
        }
    interests = _extract_known_interests(combined)
    everything = _wants_everything(combined)

    if not interests and not everything:
        options = ", ".join(sorted(KNOWN_INTEREST_TAGS))
        return {
            **state,
            "notification_triggered": False,
            "notification_message": f"which topics are you interested in? options are {options}, or say everything for all articles",
        }

    created = db.create_subscriber(email=email, frequency=frequency, interests=interests)
    if not created:
        return {
            **state,
            "notification_triggered": False,
            "notification_message": "something went wrong saving your subscription, can you try again in a bit?",
        }

    if interests:
        topics_text = ", ".join(sorted(interests))
        confirm = f"subscribed, you'll get {frequency} digests for {topics_text}"
    else:
        confirm = f"subscribed, you'll get {frequency} digests with all articles"

    return {
        **state,
        "notification_triggered": True,
        "notification_message": confirm,
    }
