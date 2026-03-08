import argparse
import os
from config.redis_config import check_redis_env_vars, test_redis_connection, clear_redis_cache


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Redis management utilities")
    parser.add_argument("--check", action="store_true", help="Check Redis environment variables")
    parser.add_argument("--test", action="store_true", help="Test Redis connection")
    parser.add_argument("--clear", action="store_true", help="Clear Redis cache")

    args = parser.parse_args()

    if args.check:
        check_redis_env_vars()

    if args.test:
        if test_redis_connection():
            print("Redis connection successful!")
        else:
            print("Redis connection failed.")

    if args.clear:
        clear_redis_cache()

    if not any([args.check, args.test, args.clear]):
        parser.print_help()