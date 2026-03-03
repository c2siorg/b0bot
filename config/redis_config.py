import redis
from dotenv import dotenv_values

env_vars = dotenv_values(".env")
REDIS_HOST = env_vars.get("REDIS_HOST", "localhost")
REDIS_PORT = int(env_vars.get("REDIS_PORT", 6379))
REDIS_PASSWORD = env_vars.get("REDIS_PASSWORD", None)
REDIS_EXPIRATION = int(env_vars.get("REDIS_EXPIRATION", 3600))  # Default cache expiry: 1 hour

redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD,
    decode_responses=True
)

def get_cache(key):
    """Get data from Redis cache"""
    try:
        return redis_client.get(key)
    except Exception as e:
        print(f"Redis get error: {e}")
        return None

def set_cache(key, value, expiration=REDIS_EXPIRATION):
    """Set data in Redis cache with expiration time"""
    try:
        redis_client.set(key, value, ex=expiration)
        return True
    except Exception as e:
        print(f"Redis set error: {e}")
        return False