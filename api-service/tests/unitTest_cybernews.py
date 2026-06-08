"""
    Unittest class for CyberNews
"""
import unittest

from cybernews.CyberNews import CyberNews


class TestCyberNews(unittest.TestCase):
    def setUp(self):
        self.news = CyberNews()
        self.valid_news = self.news.get_news_types
        self.invalid_news = ["", "Invalid"]

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
