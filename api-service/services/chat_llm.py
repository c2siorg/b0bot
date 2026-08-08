"""LLM-backed chat understanding.
Uses the same hosted CohereLabs/tiny-aya-global model (via Hugging Face's
InferenceClient, provider="cohere") already approved for article
summarization, for two jobs: classifying a chat message's intent, and
answering a question grounded on one specific article's real content.
Both return None on any failure (network, bad JSON, rate limit) so callers
can fall back to the existing keyword-based logic - this is never a hard
dependency, same as summarizer.py.
"""
import json
import logging
import os

logger = logging.getLogger(__name__)

HF_TOKEN = os.getenv("HUGGINGFACE_TOKEN")
COHERE_MODEL = "CohereLabs/tiny-aya-global"
MAX_INPUT_CHARS = 2000

VALID_INTENTS = {"search", "analyze", "subscribe", "chitchat"}

_INTENT_PROMPT = """Classify this chat message for a cybersecurity news assistant.
Return ONLY a JSON object, no other text, in this exact shape:
{{"intent": "search"|"analyze"|"subscribe"|"chitchat", "keywords": ["..."]}}

- "search": user wants to find or read about cybersecurity news/topics
- "analyze": user wants trends, sentiment, or stats about articles
- "subscribe": user wants to sign up for email alerts/digests
- "chitchat": greetings, thanks, small talk, anything with no real search intent
- "keywords": meaningful search terms only, empty list if not a search

Message: {message}"""

_GROUNDED_PROMPT = """Answer the user's question using ONLY the article content below.
Do not invent facts, dates, or details not present in the article. If the
article doesn't contain the answer, say so plainly.

Article title: {title}
Article source: {source}
Article content: {content}

Question: {question}"""


def _client():
    from huggingface_hub import InferenceClient
    return InferenceClient(provider="cohere", token=HF_TOKEN)


def classify_intent(user_input: str) -> dict | None:
    """Return {"intent", "keywords"} or None on failure."""
    if not HF_TOKEN or not user_input or not user_input.strip():
        return None
    try:
        completion = _client().chat.completions.create(
            model=COHERE_MODEL,
            messages=[{
                "role": "user",
                "content": _INTENT_PROMPT.format(message=user_input),
            }],
        )
        raw = completion.choices[0].message.content.strip()
        raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        parsed = json.loads(raw)
        if parsed.get("intent") not in VALID_INTENTS:
            return None
        return {
            "intent": parsed["intent"],
            "keywords": parsed.get("keywords") or [],
        }
    except Exception:
        logger.exception("intent classification failed, falling back to keyword matching")
        return None


def answer_grounded(article: dict, question: str) -> str | None:
    """Answer a question using only the given article's content. None on failure."""
    if not HF_TOKEN or not article or not question:
        return None
    try:
        completion = _client().chat.completions.create(
            model=COHERE_MODEL,
            messages=[{
                "role": "user",
                "content": _GROUNDED_PROMPT.format(
                    title=article.get("title", ""),
                    source=article.get("source_name", ""),
                    content=(article.get("content") or article.get("summary") or "")[:MAX_INPUT_CHARS],
                    question=question,
                ),
            }],
        )
        return completion.choices[0].message.content.strip()
    except Exception:
        logger.exception("grounded answer generation failed")
        return None
