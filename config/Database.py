from dotenv import dotenv_values
from pinecone import Pinecone
import os
import sys
import logging
from typing import Any, Optional

try:
    import redis
except ImportError:  # pragma: no cover - handled at runtime when dependency missing
    redis = None

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

PINECONE_API = dotenv_values(".env").get("PINECONE_API_KEY")

client = Pinecone(api_key=PINECONE_API)
index_name = "cybernews-index"

logger = logging.getLogger(__name__)

REDIS_URL = dotenv_values(".env").get("REDIS_URL", "redis://localhost:6379/0")
REDIS_TIMEOUT = dotenv_values(".env").get("REDIS_TIMEOUT", "5")

redis_client = None


def init_redis() -> None:
	"""Initialize the Redis client and gracefully degrade if unavailable."""
	global redis_client

	if redis is None:
		logger.warning("redis dependency not installed. Operating without Redis cache.")
		redis_client = None
		return

	try:
		timeout = int(REDIS_TIMEOUT)
	except (TypeError, ValueError):
		logger.warning(
			f"Invalid REDIS_TIMEOUT value '{REDIS_TIMEOUT}'. Falling back to 5 seconds."
		)
		timeout = 5

	try:
		redis_client = redis.from_url(
			REDIS_URL,
			decode_responses=True,
			socket_timeout=timeout,
		)
		redis_client.ping()
		logger.info("Redis connected successfully")
	except Exception as e:
		logger.warning(
			f"Redis connection failed: {e}. Operating in degraded mode (no caching)."
		)
		redis_client = None


def get_redis_client() -> Optional[Any]:
    """Return the active Redis client, or None when caching is unavailable."""
    return redis_client