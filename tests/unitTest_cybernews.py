"""
    Unittest class for CyberNews
"""
import unittest
import os
import sys

# Get the current file path
current_file_path = os.path.abspath(__file__)
src_directory = os.path.dirname(os.path.dirname(current_file_path))
sys.path.append(src_directory)

from cybernews.CyberNews import CyberNews
from unittest.mock import patch, MagicMock

class TestCyberNews(unittest.TestCase):
    def setUp(self):
        # Mock external calls to avoid real network access during init
        self.extractor_patcher = patch('cybernews.extractor.Extractor.data_extractor')
        self.rss_patcher = patch('cybernews.social_connectors.rss_extractor.RSSExtractor.process_feeds')
        
        self.mock_extractor = self.extractor_patcher.start()
        self.mock_rss = self.rss_patcher.start()
        
        self.mock_extractor.return_value = [{"id": "1", "headlines": "Test", "author": "Tester", "fullNews": "News", "newsURL": "http://test.com", "newsImgURL": "http://img.com", "newsDate": "01/01/2026"}]
        self.mock_rss.return_value = []
        
        self.news = CyberNews()
        self.valid_news = self.news.get_news_types
        self.invalid_news = ["", "Invalid"]

    def tearDown(self):
        self.extractor_patcher.stop()
        self.rss_patcher.stop()

    def test_init(self):
        self.assertIsNotNone(self.news.get_news_types)

    def test_get_news(self):
        [self.assertIsNotNone(self.news.get_news(news)) for news in self.valid_news]

    def test_get_news_invalid_type(self):
        for news in self.invalid_news:
            with self.assertRaises(ValueError):
                self.news.get_news(news)


if __name__ == "__main__":
    unittest.main()
