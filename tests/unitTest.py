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
from services.NewsService import NewsService


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
    
    def test_news_keywords_missing_parameter(self):
        """Test that missing keywords parameter returns 400 Bad Request"""
        response = self.app.get('/mistralai/news_keywords')
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn('error', data)
        self.assertIn('keywords', data['error'].lower())
    
    def test_news_keywords_empty_parameter(self):
        """Test that empty keywords parameter returns 400 Bad Request"""
        response = self.app.get('/mistralai/news_keywords?keywords=')
        self.assertEqual(response.status_code, 400)
    
    def test_invalid_route(self):
        response = self.app.get('/xxx')
        self.assertEqual(response.status_code, 404)
    
    def test_invalid_route_returns_json(self):
        """Test that 404 handler returns proper JSON response"""
        response = self.app.get('/unknown_route')
        self.assertEqual(response.status_code, 404)
        data = response.get_json()
        self.assertIsNotNone(data)
        self.assertIn('error', data)


class NewsServiceTestCase(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        # Note: NewsService requires API token, so we'll test toJSON directly
        pass
    
    def test_toJSON_with_empty_string(self):
        """Test that toJSON handles empty string input"""
        service = NewsService.__new__(NewsService)
        result = service.toJSON("")
        self.assertEqual(result, {})
    
    def test_toJSON_with_empty_list(self):
        """Test that toJSON handles data that results in empty list"""
        service = NewsService.__new__(NewsService)
        # Data with only newlines should result in empty list
        result = service.toJSON("\n\n\n")
        self.assertEqual(result, [])
        self.assertIsInstance(result, list)
    
    def test_toJSON_with_single_item(self):
        """Test that toJSON handles single news item without crashing"""
        service = NewsService.__new__(NewsService)
        # Format: header line, news items, footer line
        data = "Header line\n[Test Title, Test Source, 01/03/2026, https://test.com]\nFooter line"
        result = service.toJSON(data)
        self.assertIsInstance(result, list)
        # Should have 1 item after popping first (header) and last (footer)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['title'], 'Test Title')
        self.assertEqual(result[0]['source'], 'Test Source')
    

if __name__ == '__main__':
    unittest.main()
