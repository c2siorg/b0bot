from collections import Counter
from agents.state import PlannerState

POSITIVE_WORDS = {"fixed", "patched", "resolved", "mitigated", "secured", "updated", "protected"}
NEGATIVE_WORDS = {"vulnerability", "exploit", "attack", "breach", "ransomware", "malware", "critical", "exposed", "leaked", "compromised"}

def analyzer_agent(state: PlannerState) -> PlannerState:
    articles = state.get("retrieved_articles", [])

    if not articles:
        return {**state, "analysis": None}

    all_text = " ".join(
        (a.get("title", "") + " " + a.get("body", "")).lower()
        for a in articles
    )
    words = [w.strip(".,!?:;\"'") for w in all_text.split() if len(w) > 4]
    keyword_freq = Counter(words).most_common(10)

    trending = [word for word, count in keyword_freq if count > 1]

    word_set = set(all_text.split())
    positive_hits = word_set & POSITIVE_WORDS
    negative_hits = word_set & NEGATIVE_WORDS

    if len(negative_hits) > len(positive_hits):
        sentiment = "negative"
    elif len(positive_hits) > len(negative_hits):
        sentiment = "positive"
    else:
        sentiment = "neutral"

    analysis = {
        "keyword_frequency": keyword_freq,
        "trending_topics": trending,
        "sentiment": sentiment,
        "positive_signals": list(positive_hits),
        "negative_signals": list(negative_hits),
    }

    return {**state, "analysis": analysis}
