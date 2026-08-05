"""Article summary generation.

Tries the hosted CohereLabs/tiny-aya-global model via Hugging Face's
InferenceClient (provider="cohere") first, since it benchmarked ~3x
faster than running distilbart-cnn-12-6 locally. Falls back to the
local model if the hosted call fails or Cohere/HF is down, so summary
generation never hard-depends on an external service being up.
"""
import logging
import os

logger = logging.getLogger(__name__)

HF_TOKEN = os.getenv("HUGGINGFACE_TOKEN")
COHERE_MODEL = "CohereLabs/tiny-aya-global"
LOCAL_MODEL = "sshleifer/distilbart-cnn-12-6"
MAX_INPUT_CHARS = 2000

_local_summarizer = None


def _get_local_summarizer():
    """Lazily load the local distilbart model and tokenizer (singleton),
    only if the hosted call fails, so we don't pay the model-load cost
    on the happy path. Uses AutoModelForSeq2SeqLM directly rather than
    pipeline("summarization"), that task isn't registered in the
    installed transformers version."""
    global _local_summarizer
    if _local_summarizer is None:
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
        logger.info("loading local fallback summarizer: %s", LOCAL_MODEL)
        tokenizer = AutoTokenizer.from_pretrained(LOCAL_MODEL, token=HF_TOKEN)
        model = AutoModelForSeq2SeqLM.from_pretrained(LOCAL_MODEL, token=HF_TOKEN)
        _local_summarizer = (tokenizer, model)
    return _local_summarizer


def _summarize_with_cohere(text: str) -> str | None:
    if not HF_TOKEN:
        return None
    try:
        from huggingface_hub import InferenceClient
        client = InferenceClient(provider="cohere", token=HF_TOKEN)
        completion = client.chat.completions.create(
            model=COHERE_MODEL,
            messages=[{
                "role": "user",
                "content": f"Summarize this cybersecurity article in 2-3 sentences:\n\n{text[:MAX_INPUT_CHARS]}",
            }],
        )
        return completion.choices[0].message.content.strip()
    except Exception:
        logger.exception("cohere summary generation failed, falling back to local")
        return None


def _summarize_with_local(text: str) -> str | None:
    try:
        tokenizer, model = _get_local_summarizer()
        inputs = tokenizer(text[:MAX_INPUT_CHARS], return_tensors="pt", truncation=True, max_length=1024)
        output_ids = model.generate(
            **inputs,
            max_length=100,
            min_length=30,
            do_sample=False,
            forced_bos_token_id=0,
        )
        summary = tokenizer.decode(output_ids[0], skip_special_tokens=True)
        return summary.strip()
    except Exception:
        logger.exception("local summary generation failed")
        return None


def generate_summary(text: str) -> str | None:
    """Generate a short summary for an article. Tries the hosted model
    first, falls back to local on failure. Returns None if both fail,
    so the caller can leave the article's summary as pending and retry
    on a later batch run."""
    if not text or not text.strip():
        return None
    summary = _summarize_with_cohere(text)
    if summary:
        return summary
    return _summarize_with_local(text)
