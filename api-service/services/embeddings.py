"""Embedding generation for chat search queries.

Uses ``sentence-transformers/all-MiniLM-L6-v2`` to produce 384-dim vectors
for hybrid search in pgvector, matching the model ingestion-service uses to
embed articles.
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
    """Generate a 384-dim embedding vector for the given query text.

    Input is truncated to ~512 tokens (model max). On failure, an empty
    list is returned so the caller can fall back to keyword-only search.
    """
    if not text or not text.strip():
        return []
    try:
        model = _get_model()
        # Truncate input to avoid exceeding model context window.
        truncated = text[:MAX_TOKEN_LENGTH * 4]
        vector = model.encode(truncated, convert_to_numpy=True)
        return vector.tolist()
    except Exception:
        logger.exception("query embedding generation failed")
        return []
