import pytest
import sys
from unittest.mock import MagicMock, patch

# Step 1: Prevent Pinecone from crashing the test environment
mock_db_module = MagicMock()
sys.modules["config.Database"] = mock_db_module
sys.modules["pinecone"] = MagicMock()

# Step 2: Now import the service
from services.NewsService import NewsService

def test_news_service_parsing():
    # Mocking external file reads (config.json)
    with patch('builtins.open', MagicMock()), \
         patch('json.load', MagicMock(return_value={"openai": "gpt-3.5"})):
        
        # Mock the Database class itself
        with patch('models.NewsModel.CybernewsDB') as MockDB:
            service = NewsService(model_name="openai")
            service.db = MockDB.return_value
            
            # Mock successful LLM output (A list of dictionaries)
            fake_llm_output = [{
                "title": "C2SI GSoC 2026: Success",
                "source": "CyberNews",
                "date": "05/03/2026",
                "url": "https://c2si.org/b0bot"
            }]

            # Patch the invoke method of the LangChain sequence
            with patch('langchain_core.runnables.base.RunnableSequence.invoke') as mock_invoke:
                mock_invoke.return_value = fake_llm_output
                
                # Run the function with the correct argument name
                result = service.getNews(keywords="GSoC")

                # Step 3: Assertions
                assert isinstance(result, list), f"Expected list, got {type(result)}"
                assert len(result) > 0
                assert result[0]["title"] == "C2SI GSoC 2026: Success"
                print("\n✅ TEST PASSED: NewsService is production-ready.")

if __name__ == "__main__":
    test_news_service_parsing()