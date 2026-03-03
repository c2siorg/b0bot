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
    
    def test_invalid_route(self):
        response = self.app.get('/xxx')
        self.assertEqual(response.status_code, 404)
    

if __name__ == '__main__':
    unittest.main()
