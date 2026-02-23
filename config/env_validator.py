import os

REQUIRED_ENV_VARS = [
    "PINECONE_API_KEY",
    "HUGGINGFACE_TOKEN"
]

def validate_env():
    """
    Validates that all required environment variables are set.
    Raises RuntimeError if any are missing.
    """
    missing_vars = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]

    if missing_vars:
        raise RuntimeError(
            f"Missing required environment variables: {', '.join(missing_vars)}"
        )