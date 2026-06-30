"""Embedding generation for article ingestion.

Uses ``sentence-transformers/all-MiniLM-L6-v2`` to produce 384-dim vectors
for hybrid search in pgvector.
"""
import logging
import os

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "sentence-transformers/all-MiniLM-L6-v2",
)
EMBEDDING_DIM = 384
MAX_TOKEN_LENGTH = 512

_model = None


def _get_model():
    """Lazily load the sentence-transformers model (singleton)."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        logger.info("loading embedding model: %s", EMBEDDING_MODEL)
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


def generate_embedding(text: str) -> list[float]:
    """Generate a 384-dim embedding vector for the given text.

    Input is truncated to ~512 tokens (model max). On failure, an empty
    list is returned so the caller can mark ``embedding_status=failed``.
    """
    if not text or not text.strip():
        text = "empty"
    try:
        model = _get_model()
        # Truncate input to avoid exceeding model context window.
        truncated = text[:MAX_TOKEN_LENGTH * 4]
        vector = model.encode(truncated, convert_to_numpy=True)
        return vector.tolist()
    except Exception:
        logger.exception("embedding generation failed")
        return []


def prepare_embedding_text(title: str, snippet: str) -> str:
    """Combine title + snippet for embedding input."""
    return f"{title} {snippet}".strip()