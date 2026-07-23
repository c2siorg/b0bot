import re
from collections import Counter

from bs4 import BeautifulSoup

from agents.state import PlannerState

SENTIMENT_MODEL = "distilbert-base-uncased-finetuned-sst-2-english"
NEUTRAL_THRESHOLD = 0.55

# WordPress-style RSS feeds append a syndication credit line to the article
# body, not real content, just noise in keyword frequency and sentiment
# input. Covers the common phrasings we've actually seen across sources.
SYNDICATION_PATTERNS = [
    re.compile(r"the post .*? appeared first on .*?\.", re.IGNORECASE),
    re.compile(r"originally (published|appeared) (at|on) .*?\.", re.IGNORECASE),
]

try:
    from transformers import pipeline
    sentiment_pipeline = pipeline(
        "text-classification",
        model=SENTIMENT_MODEL,
        truncation=True,
        max_length=128,
    )
except (ImportError, OSError, RuntimeError):
    sentiment_pipeline = None


def _strip_html(text: str) -> str:
    if not text:
        return ""
    clean = BeautifulSoup(text, "html.parser").get_text()
    for pattern in SYNDICATION_PATTERNS:
        clean = pattern.sub("", clean)
    return clean


def _classify(text: str) -> tuple[str, float]:
    if not sentiment_pipeline or not text.strip():
        return "neutral", 0.0

    result = sentiment_pipeline(text)[0]
    label = result["label"].lower()
    score = result["score"]

    if score < NEUTRAL_THRESHOLD:
        return "neutral", score
    return label, score


def analyzer_agent(state: PlannerState) -> PlannerState:
    articles = state.get("retrieved_articles", [])

    if not articles:
        return {**state, "analysis": None}

    all_text = " ".join(
        (a.get("title", "") + " " + _strip_html(a.get("body", ""))).lower()
        for a in articles
    )
    words = [w.strip(".,!?:;\"'") for w in all_text.split() if len(w) > 4]
    keyword_freq = Counter(words).most_common(10)
    trending = [word for word, count in keyword_freq if count > 1]

    article_sentiments = []
    for a in articles:
        text = (a.get("title", "") + ". " + _strip_html(a.get("body", ""))).strip()
        label, score = _classify(text)
        article_sentiments.append({
            "title": a.get("title", ""),
            "sentiment": label,
            "confidence": round(score, 3),
        })

    labels = [s["sentiment"] for s in article_sentiments]
    label_counts = Counter(labels)
    overall_sentiment = label_counts.most_common(1)[0][0] if label_counts else "neutral"

    confidences = [s["confidence"] for s in article_sentiments if s["confidence"] > 0]
    avg_confidence = round(sum(confidences) / len(confidences), 3) if confidences else 0.0

    analysis = {
        "keyword_frequency": keyword_freq,
        "trending_topics": trending,
        "sentiment": overall_sentiment,
        "sentiment_confidence": avg_confidence,
        "article_sentiments": article_sentiments,
    }

    return {**state, "analysis": analysis}
