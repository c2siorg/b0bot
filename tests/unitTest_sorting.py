import unittest

from cybernews.sorting import Sorting


class TestSorting(unittest.TestCase):
    def setUp(self):
        self.sorting = Sorting()

    def test_ordering_news_prefers_news_date_over_existing_id(self):
        news = [
            {"id": 9999999999, "headlines": "older", "newsDate": "January 01, 2024"},
            {"id": 2, "headlines": "newer", "newsDate": "January 01, 2025"},
            {"id": 3, "headlines": "unknown", "newsDate": "N/A"},
        ]

        ordered = self.sorting.ordering_news(news)
        headlines = [item["headlines"] for item in ordered]

        self.assertEqual(headlines[0], "newer")
        self.assertEqual(headlines[1], "older")
        self.assertEqual(headlines[2], "unknown")

    def test_ordering_news_assigns_unique_ids(self):
        news = [
            {"id": 1, "headlines": "a", "newsDate": "N/A"},
            {"id": 2, "headlines": "b", "newsDate": "N/A"},
            {"id": 3, "headlines": "c", "newsDate": "N/A"},
        ]

        ordered = self.sorting.ordering_news(news)
        generated_ids = [item["id"] for item in ordered]

        self.assertEqual(len(generated_ids), len(set(generated_ids)))


if __name__ == "__main__":
    unittest.main()
