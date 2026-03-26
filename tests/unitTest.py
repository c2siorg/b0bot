import unittest
from unittest.mock import MagicMock, patch

from dotenv import load_dotenv
import os
import sys

# Get the current file path
current_file_path = os.path.abspath(__file__)

# Get the grandparent directory
src_directory = os.path.dirname(os.path.dirname(current_file_path))

# Add the parent directory to sys.path
sys.path.append(src_directory)

dotenv_path = os.path.join(src_directory, '.env')
load_dotenv(dotenv_path)

# Import the Flask application
from app import app


class FlaskAppTestCase(unittest.TestCase):
    def setUp(self):
        self.controller_patcher = patch("routes.NewsRoutes.NewsController")
        mocked_controller_cls = self.controller_patcher.start()

        mocked_controller = MagicMock()
        mocked_controller.getNews.return_value = [
            {
                "title": "Sample Title",
                "source": "Sample Source",
                "date": "01/01/2026",
                "url": "https://example.com",
            }
        ]
        mocked_controller.getNewsWithKeywords.return_value = mocked_controller.getNews.return_value
        mocked_controller.notFound.return_value = ("Not Found", 404)
        mocked_controller_cls.return_value = mocked_controller

        # Create a test client
        self.app = app.test_client()
        self.app.testing = True
        
    def tearDown(self):
        self.controller_patcher.stop()
    
    def test_news(self):
        """Ensure raw news endpoint returns a successful response."""
        response = self.app.get('/raw/news')
        self.assertEqual(response.status_code, 200)
    
    def test_news_keywords(self):
        """Ensure keyword endpoint succeeds with a valid keyword argument."""
        response = self.app.get('/raw/news_keywords?keywords=firewall')
        self.assertEqual(response.status_code, 200)

    def test_news_keywords_missing_query(self) -> None:
        """Return 400 when the required keyword query parameter is missing."""
        response = self.app.get('/raw/news_keywords')
        self.assertEqual(response.status_code, 400)
        self.assertIn("Missing query parameter: keywords", response.get_data(as_text=True))

    def test_news_keywords_blank_query(self) -> None:
        """Return 400 when the keyword parameter is present but blank."""
        response = self.app.get('/raw/news_keywords?keywords=')
        self.assertEqual(response.status_code, 400)
        self.assertIn("Missing query parameter: keywords", response.get_data(as_text=True))
    
    def test_invalid_route(self):
        """Ensure unknown routes are handled by the 404 route handler."""
        response = self.app.get('/xxx/invalid')
        self.assertEqual(response.status_code, 404)
        self.assertIn("Not Found", response.get_data(as_text=True))
    

if __name__ == '__main__':
    unittest.main()
