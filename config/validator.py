import os
from dotenv import dotenv_values

class ConfigurationError(Exception):
    """Custom exception raised for missing required environment variables."""
    pass

def validate_env():
    """Validates that all strictly required environment variables are present."""
    # Priority: os.environ, then fallback to .env file
    # We collect all available vars to check existence
    env_file_path = ".env"
    env_file_exists = os.path.exists(env_file_path)
    
    # Load .env values for a complete picture, but os.environ takes precedence
    file_vars = dotenv_values(env_file_path) if env_file_exists else {}
    env_vars = {**file_vars, **os.environ}
    
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
        error_msg = (
            f"Missing required environment variables: {', '.join(missing_keys)}. "
            "Please ensure they are set in your environment or .env file."
        )
        if not env_file_exists:
            error_msg += f" Note: {env_file_path} file was not found."
            
        raise ConfigurationError(error_msg)
