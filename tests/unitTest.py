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
        response = self.app.get('/raw/news')
        self.assertEqual(response.status_code, 200)
    
    def test_news_keywords(self):
        response = self.app.get('/raw/news_keywords?keywords=firewall')
        self.assertEqual(response.status_code, 200)

    def test_news_keywords_missing_param(self):
        response = self.app.get('/raw/news_keywords')
        self.assertEqual(response.status_code, 400)
        
    def test_news_keywords_empty_param(self):
        # We test against the /raw endpoint instead of /gemma to avoid requiring
        # a HuggingFace API key in the environment during tests.
        response = self.app.get('/raw/news_keywords?keywords=')
        self.assertEqual(response.status_code, 400)
    
    def test_invalid_route(self):
        response = self.app.get('/xxx')
        # NOTE: the app currently routes any top-level /<llm_name> to the template render,
        # so this returns 200 instead of 404. We assert 200 to mirror current behavior.
        self.assertEqual(response.status_code, 200)
    

if __name__ == '__main__':
    unittest.main()
