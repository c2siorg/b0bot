import os
from dotenv import dotenv_values

class ConfigurationError(Exception):
    """Custom exception raised for missing required environment variables."""
    pass

def validate_env():
    """Validates that all strictly required environment variables are present."""
    # First check os.environ, then fallback to .env file
    env_vars = {**dotenv_values(".env"), **os.environ}
    
    required_keys = [
        "PINECONE_API_KEY",
        "PINECONE_INDEX_NAME"
    ]
    
    missing_keys = []
    for key in required_keys:
        if not env_vars.get(key):
            missing_keys.append(key)
            
    # For HF, we need either HUGGINGFACE_TOKEN or HF_TOKEN
    hf_token = env_vars.get("HUGGINGFACE_TOKEN") or env_vars.get("HF_TOKEN")
    if not hf_token:
        missing_keys.append("HUGGINGFACE_TOKEN or HF_TOKEN")
        
    if missing_keys:
        raise ConfigurationError(
            f"Missing required environment variables: {', '.join(missing_keys)}. "
            "Please check your .env file."
        )
