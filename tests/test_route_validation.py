import unittest
from unittest.mock import patch

from app import app


class TestRouteValidation(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_invalid_model_page_returns_404_with_error_message(self):
        response = self.client.get("/invalid-model")
        self.assertEqual(response.status_code, 404)
        self.assertIn(b"Unsupported model", response.data)

    def test_news_keywords_missing_query_returns_400(self):
        response = self.client.get("/mistralai/news_keywords")
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"Please provide a non-empty", response.data)

    def test_news_keywords_blank_query_returns_400(self):
        response = self.client.get("/mistralai/news_keywords?keywords=")
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"Please provide a non-empty", response.data)

    @patch("routes.NewsRoutes.NewsController")
    def test_news_service_value_error_returns_400(self, controller_cls_mock):
        controller_mock = controller_cls_mock.return_value
        controller_mock.getNews.side_effect = ValueError("Model misconfigured")

        response = self.client.get("/mistralai/news")
        self.assertEqual(response.status_code, 400)
        payload = response.get_json()
        self.assertEqual(payload.get("error"), "Model misconfigured")

    @patch("routes.NewsRoutes.NewsController")
    def test_news_keywords_success_uses_trimmed_keyword(self, controller_cls_mock):
        controller_mock = controller_cls_mock.return_value
        controller_mock.getNewsWithKeywords.return_value = []

        response = self.client.get("/mistralai/news_keywords?keywords=%20phishing%20")
        self.assertEqual(response.status_code, 200)
        controller_mock.getNewsWithKeywords.assert_called_once_with("phishing")


if __name__ == "__main__":
    unittest.main()
