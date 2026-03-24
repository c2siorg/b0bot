import unittest
import os
import sys

# Ensure root directory is in sys.path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# Set dummy environment variables to bypass initialization errors
os.environ['PINECONE_API_KEY'] = 'dummy-key'
os.environ['HUGGINGFACE_TOKEN'] = 'dummy-token'
os.environ['PINECONE_INDEX_NAME'] = 'dummy-index'

# Mock external dependencies
from unittest.mock import patch, MagicMock

# 1. Mock embedding models GLOBALLY before they are imported anywhere
import sentence_transformers
patch('sentence_transformers.SentenceTransformer', return_value=MagicMock()).start()
# SparseEncoder is often a separate class in some versions, but we'll mock it where imported
patch('sentence_transformers.SparseEncoder', return_value=MagicMock()).start()

# 2. Mock Pinecone Client in config.Database
import config.Database
mock_client = MagicMock()
config.Database.client = mock_client
# Also mock some internal methods that might be called during init
mock_client.Index.return_value = MagicMock()

# 3. Mock HuggingFaceEndpoint in NewsService
import services.NewsService
patch.object(services.NewsService, 'HuggingFaceEndpoint').start()

# Import the Flask application
from app import app


class FlaskAppTestCase(unittest.TestCase):
    def setUp(self):
        # Create a test client
        self.app = app.test_client()
        
    def tearDown(self):
        pass
    
    @patch('services.NewsService.NewsService.getNews')
    def test_news(self, mock_get_news):
        mock_get_news.return_value = [{"title": "Test News", "source": "Test", "date": "01/01/2026", "url": "http://test.com"}]
        response = self.app.get('/raw/news')
        self.assertEqual(response.status_code, 200)
    
    @patch('services.NewsService.NewsService.getNews')
    def test_news_keywords(self, mock_get_news):
        mock_get_news.return_value = [{"title": "Keyword News", "source": "Test", "date": "01/01/2026", "url": "http://test.com"}]
        response = self.app.get('/raw/news_keywords?keywords=firewall')
        self.assertEqual(response.status_code, 200)
    
    def test_invalid_route(self):
        response = self.app.get('/this/route/really/does/not/exist')
        self.assertEqual(response.status_code, 404)
    
    @patch('services.NewsService.LLMChain')
    @patch('config.Database.SemanticCache.get')
    def test_cache_hit(self, mock_cache_get, mock_llm_chain_cls):
        # Mock a cache hit
        mock_cache_get.return_value = [{"title": "Cached News", "source": "Cache", "date": "01/01/2026", "url": "http://cache.com"}]
        
        response = self.app.get('/mistralai/news')
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Cached News", response.data)
        # Verify LLM chain was NOT even instantiated
        mock_llm_chain_cls.assert_not_called()

    @patch('services.NewsService.LLMChain')
    @patch('config.Database.SemanticCache.get')
    @patch('config.Database.SemanticCache.set')
    def test_cache_miss(self, mock_cache_set, mock_cache_get, mock_llm_chain_cls):
        # Mock a cache miss
        mock_cache_get.return_value = None
        # Mock LLM chain instance and its invoke method
        mock_chain_instance = MagicMock()
        mock_llm_chain_cls.return_value = mock_chain_instance
        mock_chain_instance.invoke.return_value = {"text": "[Test News, Test Source, 01/01/2026, http://test.com];\n[ [Test News, Test Source, 01/01/2026, http://test.com] ];\n"}
        
        response = self.app.get('/mistralai/news')
        
        self.assertEqual(response.status_code, 200)
        # Verify LLM chain WAS instantiated and invoked
        mock_llm_chain_cls.assert_called_once()
        mock_chain_instance.invoke.assert_called_once()
        # Verify result WAS cached
        mock_cache_set.assert_called_once()
    

if __name__ == '__main__':
    unittest.main()
