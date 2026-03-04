import json
import os
import redis
from dotenv import load_dotenv
load_dotenv()

class RedisClient:
    def __init__(self,expiry:int = 3600):
        # Load environment variables

        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = int(os.getenv("REDIS_PORT", 6379))
        redis_password = os.getenv("REDIS_PASSWORD", None)

        # Initialize Redis connection
        self.redis = redis.Redis(
            host=redis_host,
            port=redis_port,
            password=redis_password,
            decode_responses=True
        )

        # Default expiration time (1 hour)
        self.default_expiry = expiry

    def set(self, key, value, expiry=None):
        try:
            # Serialize complex data structures
            if not isinstance(value, (str, int, float, bool)):
                value = json.dumps(value)

            # Store with expiry if provided
            if expiry is None:
                expiry = self.default_expiry

            return self.redis.setex(key, expiry, value)
        except Exception as e:
            print(f"Redis error setting {key}: {e}")
            return False

    def get(self, key):
        try:
            value = self.redis.get(key)
            if value is None:
                return None

            # Try to deserialize JSON, return as-is if not valid JSON
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        except Exception as e:
            print(f"Redis error getting {key}: {e}")
            return None

    def delete(self, key):
        return self.redis.delete(key)

    def exists(self, key):
        return bool(self.redis.exists(key))

    def flush_all(self):
        return self.redis.flushdb()