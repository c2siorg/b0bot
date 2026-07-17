"""
Tests for input validation and error handling — PR #188
Addresses issue #140: Lack of input sanitisation on keywords endpoint
"""
import pytest
from unittest.mock import patch
from app import app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


# --- Keyword sanitisation tests (Issue #140) ---

def test_empty_keyword_returns_400(client):
    res = client.get('/llama/news_keywords?keywords=')
    assert res.status_code == 400
    data = res.get_json()
    assert 'error' in data

def test_missing_keyword_param_returns_400(client):
    res = client.get('/llama/news_keywords')
    assert res.status_code == 400

def test_script_injection_is_rejected(client):
    res = client.get('/llama/news_keywords?keywords=<script>alert(1)</script>')
    assert res.status_code == 400

def test_sql_injection_is_rejected(client):
    res = client.get('/llama/news_keywords?keywords=DROP TABLE users')
    assert res.status_code == 400

def test_valid_keyword_does_not_crash(client):
    with patch('controllers.news_controller.NewsController.get_news_by_keyword') as mock:
        mock.return_value = {"news": "test"}
        res = client.get('/llama/news_keywords?keywords=ransomware')
        assert res.status_code != 500


# --- LLM name validation ---

def test_invalid_llm_name_returns_error(client):
    res = client.get('/fakellm/news')
    assert res.status_code in [400, 404]

def test_valid_llm_llama(client):
    with patch('controllers.news_controller.NewsController.get_news') as mock:
        mock.return_value = {"news": "test"}
        res = client.get('/llama/news')
        assert res.status_code != 404


# --- Global error handling ---

def test_404_returns_json_not_html(client):
    res = client.get('/this/route/does/not/exist')
    assert res.status_code == 404
    data = res.get_json()
    assert data is not None
    assert 'error' in data

def test_health_endpoint_exists(client):
    res = client.get('/health')
    assert res.status_code == 200
