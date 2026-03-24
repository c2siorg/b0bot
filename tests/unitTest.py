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
    

if __name__ == '__main__':
    unittest.main()
