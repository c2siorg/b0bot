import os
import unittest
from unittest.mock import patch

# Ensure basic env keys exist so app imports in test environments.
os.environ.setdefault("HUGGINGFACE_TOKEN", "test-token")
os.environ.setdefault("PINECONE_API_KEY", "test-key")

from app import app


class TestHealthRoutes(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_health_route_returns_200(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)

        payload = response.get_json()
        self.assertIsInstance(payload, dict)
        self.assertEqual(payload.get("status"), "ok")
        self.assertEqual(payload.get("service"), "b0bot")
        self.assertIn("timestamp", payload)

    @patch("routes.NewsRoutes.get_readiness_payload")
    def test_ready_route_returns_200_when_ready(self, readiness_mock):
        readiness_mock.return_value = {
            "status": "ready",
            "timestamp": "2026-01-01T00:00:00Z",
            "checks": {},
            "errors": [],
        }

        response = self.client.get("/ready")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json().get("status"), "ready")

    @patch("routes.NewsRoutes.get_readiness_payload")
    def test_ready_route_returns_503_when_not_ready(self, readiness_mock):
        readiness_mock.return_value = {
            "status": "not-ready",
            "timestamp": "2026-01-01T00:00:00Z",
            "checks": {},
            "errors": ["Missing required environment variables"],
        }

        response = self.client.get("/ready")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.get_json().get("status"), "not-ready")

    def test_not_found_route_returns_json_404(self):
        response = self.client.get("/route-that-does-not-exist")
        self.assertEqual(response.status_code, 404)

        payload = response.get_json()
        self.assertIsInstance(payload, dict)
        self.assertEqual(payload.get("error"), "Not Found")


if __name__ == "__main__":
    unittest.main()
