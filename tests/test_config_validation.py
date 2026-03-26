import os
import pytest
from unittest.mock import patch
from config.validator import validate_env, ConfigurationError

# Mock environment variables before importing app to prevent SystemExit during test collection
os.environ["PINECONE_API_KEY"] = "test_pinecone_key"
os.environ["PINECONE_INDEX_NAME"] = "test_index"
os.environ["HUGGINGFACE_TOKEN"] = "test_hf_token"

from app import app

def test_validate_env_missing_keys():
    # Clear environment variables to simulate missing keys
    with patch.dict(os.environ, {}, clear=True), patch('config.validator.dotenv_values', return_value={}):
        with pytest.raises(ConfigurationError) as exc_info:
            validate_env()
        assert "Missing required environment variables" in str(exc_info.value)
        assert "PINECONE_API_KEY" in str(exc_info.value)
        assert "PINECONE_INDEX_NAME" in str(exc_info.value)

def test_validate_env_success():
    mock_env = {
        "PINECONE_API_KEY": "test_pinecone_key",
        "PINECONE_INDEX_NAME": "test_index",
        "HUGGINGFACE_TOKEN": "test_hf_token"
    }
    with patch.dict(os.environ, mock_env, clear=True), patch('config.validator.dotenv_values', return_value={}):
        # Should not raise any exception
        validate_env()

def test_global_error_handler():
    # Configure the app for testing
    app.config['TESTING'] = True
    client = app.test_client()
    
    # We can mock a route or trigger an error by making an invalid request
    # To test the error handler, we purposely raise an exception in a test route
    
    @app.route('/test-error')
    def test_error_route():
        raise ValueError("Simulated random error")
        
    response = client.get('/test-error')
    assert response.status_code == 500
    assert response.is_json
    data = response.get_json()
    assert "error" in data
    assert "Simulated random error" in data["error"]
    assert data["code"] == 500
