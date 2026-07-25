"""Central configuration for ingestion-service.

Environment-backed settings and shared constants live here so poller, worker,
handler, and db modules do not duplicate defaults.
"""
import os

# ─── Queue / Redis ────────────────────────────────────────────────────────────
ARTICLE_DISCOVERED_QUEUE = os.getenv("ARTICLE_DISCOVERED_QUEUE", "article-discovered")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

# ─── RSS polling ──────────────────────────────────────────────────────────────
POLLING_INTERVAL_SECONDS = int(os.getenv("POLLING_INTERVAL_SECONDS", "900"))
RSS_FEED_TIMEOUT = int(os.getenv("RSS_FEED_TIMEOUT", "10"))
RSS_USER_AGENT = os.getenv("RSS_USER_AGENT", "B0Bot/1.0")

# ─── Postgres ─────────────────────────────────────────────────────────────────
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://b0bot:b0bot@postgres:5432/b0bot",
)

# ─── Embeddings ───────────────────────────────────────────────────────────────
EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "sentence-transformers/all-MiniLM-L6-v2",
)
EMBEDDING_DIM = 384
MAX_EMBEDDING_INPUT_CHARS = 512 * 4  # ~512 tokens for MiniLM

# ─── article.discovered event contract ────────────────────────────────────────
EVENT_ARTICLE_DISCOVERED = "article.discovered"
ARTICLE_SCHEMA_VERSION = 1
DEFAULT_ARTICLE_LANGUAGE = "en"

# ─── URL normalization / parsing ────────────────────────────────────────────────
CONTENT_SNIPPET_MAX_LEN = 500
TRACKING_QUERY_PREFIXES = ("utm_", "fbclid", "gclid", "ref", "source")


def article_idempotency_key(url_hash: str) -> str:
    """Build the idempotency key for a discovered article."""
    return f"article:{url_hash}:discovered"
