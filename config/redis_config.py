import os
import redis
from dotenv import load_dotenv, find_dotenv

def check_redis_env_vars():
    # Load current environment variables
    load_dotenv(find_dotenv())

    # Check if Redis variables exist
    redis_vars = ["REDIS_HOST", "REDIS_PORT", "REDIS_PASSWORD"]
    missing_vars = [var for var in redis_vars if os.getenv(var) is None]

    if missing_vars:
        raise EnvironmentError(
            f"Missing Redis configuration variables: {', '.join(missing_vars)}.\n"
            f"Please add them to your .env file:\n"
            f"REDIS_HOST=localhost\n"
            f"REDIS_PORT=6379\n"
            f"REDIS_PASSWORD="
        )


def get_redis_client():
    # Ensure environment variables are loaded
    load_dotenv(find_dotenv())

    # Get Redis configuration from environment
    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = int(os.getenv("REDIS_PORT", 6379))
    redis_password = os.getenv("REDIS_PASSWORD", None)

    # Create Redis client
    client = redis.Redis(
        host=redis_host,
        port=redis_port,
        password=redis_password if redis_password else None,
        decode_responses=True
    )

    return client


def test_redis_connection():
    try:
        client = get_redis_client()
        return client.ping()
    except EnvironmentError as e: # if there is a problem with the environment variables
        print(f"Redis configuration error: {e}")
        return False
    except Exception as e:
        print(f"Redis connection error: {e}")
        return False


def clear_redis_cache():
    try:
        client = get_redis_client()
        client.flushdb()
        print("Successfully cleared Redis cache")
        return True
    except Exception as e:
        print(f"Error clearing Redis cache: {e}")
        return False