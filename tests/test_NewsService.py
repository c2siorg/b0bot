import pytest
import sys
import os
from unittest.mock import MagicMock, patch

# --- STEP 1: PATH & MODULE FIXES ---
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock the dependency that NewsService imports
mock_agent_tools = MagicMock()
sys.modules["services.AgentTools"] = mock_agent_tools
sys.modules["pinecone"] = MagicMock()
sys.modules["config.Database"] = MagicMock()

# Now we can import the service
from services.NewsService import NewsService

def test_news_service_parsing():
    # Setup the mock data for fetch_cyber_news.invoke()
    fake_raw_data = [{
        "title": "C2SI GSoC 2026: Success",
        "source": "CyberNews",
        "date": "05/03/2026",
        "url": "https://c2si.org/b0bot"
    }]
    
    # Configure the mock to return our fake data
    mock_agent_tools.fetch_cyber_news.invoke.return_value = fake_raw_data

    # Call the static method
    result = NewsService.get_consolidated_news(["GSoC"])

    # --- ASSERTIONS ---
    assert isinstance(result, list)
    assert len(result) > 0
    assert result[0]["title"] == "C2SI GSoC 2026: Success"
    
    print("\n✅ TEST PASSED: 'get_consolidated_news' is working perfectly.")

if __name__ == "__main__":
    test_news_service_parsing()