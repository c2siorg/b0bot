import pytest
from unittest.mock import MagicMock, patch
from services.NewsService import NewsService

def test_news_service_parsing():
    """
    Test that NewsService correctly handles LLM output 
    and returns a structured list.
    """
    # Initialize service
    # We use a dummy model name since we are mocking the LLM call anyway
    service = NewsService(model_name="mistral")
    
    # Define a fake LLM response that matches your Pydantic/JSON logic
    fake_llm_output = [
        {
            "title": "C2SI GSoC 2026: The Future of b0bot",
            "source": "CyberNews",
            "date": "05/03/2026",
            "url": "https://c2si.org/b0bot"
        }
    ]

    # We 'patch' the chain.invoke method so it doesn't try to go online
    with patch('langchain_core.runnables.base.RunnableSequence.invoke') as mock_invoke:
        mock_invoke.return_value = fake_llm_output
        
        # Execute the service logic
        # Even though we mock the DB, we want to ensure the logic flows
        service.db.get_news_collections = MagicMock(return_value=[{"raw": "data"}])
        
        result = service.getNews(user_keywords="GSoC")

        # ASSERTIONS: The proof for the maintainers
        assert isinstance(result, list)
        assert len(result) > 0
        assert result[0]["title"] == "C2SI GSoC 2026: The Future of b0bot"
        print("\n✅ NewsService Unit Test: SUCCESS")

if __name__ == "__main__":
    test_news_service_parsing()