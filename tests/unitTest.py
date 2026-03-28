import unittest
from flask import Flask
from flask.testing import FlaskClient

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
        # Create a test client
        self.app = app.test_client()
        
    def tearDown(self):
        pass
    
    def test_news(self):
        response = self.app.get('/news')
        self.assertEqual(response.status_code, 200)
    
    def test_news_keywords(self):
        response = self.app.get('/news_keywords?keywords=firewall')
        self.assertEqual(response.status_code, 200)

    # ── Input sanitisation tests (issue #140) ─────────────────────────────────

    def test_keywords_missing_param(self):
        """No ?keywords= param should return 400, not crash with IndexError."""
        response = self.app.get('/mistralai/news_keywords')
        self.assertEqual(response.status_code, 400)

    def test_keywords_empty_string(self):
        """Blank keyword after stripping should return 400."""
        response = self.app.get('/mistralai/news_keywords?keywords=   ')
        self.assertEqual(response.status_code, 400)

    def test_keywords_too_long(self):
        """Keyword exceeding 200 characters should return 400."""
        long_keyword = 'a' * 201
        response = self.app.get(f'/mistralai/news_keywords?keywords={long_keyword}')
        self.assertEqual(response.status_code, 400)

    def test_raw_keywords_missing_param(self):
        """Raw endpoint also returns 400 when ?keywords= is missing."""
        response = self.app.get('/raw/news_keywords')
        self.assertEqual(response.status_code, 400)

    def test_invalid_route(self):
        response = self.app.get('/xxx')
        self.assertEqual(response.status_code, 404)
    

if __name__ == '__main__':
    unittest.main()
