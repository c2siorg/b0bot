import os
import redis
from datetime import timedelta

# Read from environment variables
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")  
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))  
REDIS_DB = int(os.getenv("REDIS_DB", 0))  
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None) 

# Create Redis client
redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    password=REDIS_PASSWORD,
    decode_responses=True,  
)

# Cache Time-to-Live
CACHE_TTL = timedelta(hours=1)