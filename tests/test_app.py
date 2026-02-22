import unittest
from unittest.mock import patch, MagicMock
import os
import sys
from dotenv import load_dotenv

# Get the current file path
current_file_path = os.path.abspath(__file__)
src_directory = os.path.dirname(os.path.dirname(current_file_path))
sys.path.append(src_directory)

# Load env variables
dotenv_path = os.path.join(src_directory, '.env')
load_dotenv(dotenv_path)

# We must patch Pinecone BEFORE importing the app.
patcher_pinecone = patch('pinecone.Pinecone')
mock_pinecone_class = patcher_pinecone.start()

# Now it is safe to import the Flask application
from app import app

class TestFlaskApp(unittest.TestCase):
    @classmethod
    def tearDownClass(cls):
        patcher_pinecone.stop()

    def setUp(self):
        self.app = app.test_client()
        
    def tearDown(self):
        pass
    
    # Patch LLMChain directly so Pydantic doesn't validate the mocked LLM
    @patch('services.NewsService.HuggingFaceEndpoint')
    @patch('services.NewsService.LLMChain')
    @patch('models.NewsModel.CybernewsDB.get_news_collections')
    def test_news(self, mock_get_news, mock_llm_chain_class, mock_hf):
        mock_get_news.return_value = [{"title": "DB News", "source": "test", "newsDate": "2024", "url": "url"}]
        
        # Create a fake chain instance that returns our JSON string
        mock_chain_instance = MagicMock()
        mock_chain_instance.invoke.return_value = {'text': '\n["Mock News Title", "Mock Source", "01/01/2024", "http://mock.url"];\n'}
        mock_llm_chain_class.return_value = mock_chain_instance

        response = self.app.get('/mistralai/news')
        self.assertEqual(response.status_code, 200)
    
    @patch('services.NewsService.HuggingFaceEndpoint')
    @patch('services.NewsService.LLMChain')
    @patch('models.NewsModel.CybernewsDB.get_news_collections')
    def test_news_keywords(self, mock_get_news, mock_llm_chain_class, mock_hf):
        mock_get_news.return_value = [{"title": "DB News", "source": "test", "newsDate": "2024", "url": "url"}]
        
        mock_chain_instance = MagicMock()
        mock_chain_instance.invoke.return_value = {'text': '\n["Mock Firewall Title", "Mock Source", "01/01/2024", "http://mock.url"];\n'}
        mock_llm_chain_class.return_value = mock_chain_instance

        response = self.app.get('/mistralai/news_keywords?keywords=firewall')
        self.assertEqual(response.status_code, 200)
    
    def test_invalid_route(self):
        # Request a truly invalid route so the app hits the 404 handler
        response = self.app.get('/mistralai/invalid_endpoint_that_does_not_exist')
        self.assertEqual(response.status_code, 404)
    
if __name__ == '__main__':
    unittest.main()