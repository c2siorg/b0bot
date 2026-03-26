import unittest
from unittest.mock import MagicMock, patch
import json
import os
import sys

# Get the current file path
current_file_path = os.path.abspath(__file__)

# Get the grandparent directory
src_directory = os.path.dirname(os.path.dirname(current_file_path))

# Add the parent directory to sys.path
sys.path.append(src_directory)

from services.NewsService import NewsService  # noqa: E402


class RedisQueryCacheTestCase(unittest.TestCase):
    def setUp(self) -> None:
        """Create a lightweight NewsService instance and mock db dependency."""
        self.db_patcher = patch("services.NewsService.CybernewsDB")
        mocked_db_cls = self.db_patcher.start()

        self.service = NewsService()
        self.service.db = mocked_db_cls.return_value

    def tearDown(self) -> None:
        """Stop all active patchers after each test."""
        self.db_patcher.stop()

    def test_normalize_keyword_variants(self) -> None:
        """Ensure normalization is case-insensitive and strips punctuation noise."""
        self.assertEqual(self.service._normalize_keyword("Firewall"), "firewall")
        self.assertEqual(self.service._normalize_keyword("FIREWALL!!"), "firewall")
        self.assertEqual(self.service._normalize_keyword("fire   wall"), "fire wall")

    def test_build_cache_key_deterministic(self) -> None:
        """Ensure semantically identical keywords map to the same cache key."""
        key_one = self.service._build_cache_key("Firewall")
        key_two = self.service._build_cache_key("FIREWALL!!")
        self.assertEqual(key_one, key_two)
        self.assertTrue(key_one.startswith("b0bot:news:none:"))

    @patch("services.NewsService.get_redis_client")
    def test_get_from_cache_hit(self, mock_get_redis) -> None:
        """Return parsed JSON result on Redis cache hit."""
        cached_data = [{"title": "Sample", "source": "S", "date": "01/01/2026", "url": "u"}]
        mock_client = MagicMock()
        mock_client.get.return_value = json.dumps(cached_data)
        mock_get_redis.return_value = mock_client

        result = self.service._get_from_cache("some-key")

        self.assertEqual(result, cached_data)
        mock_client.get.assert_called_once_with("some-key")

    @patch("services.NewsService.get_redis_client")
    def test_get_from_cache_miss(self, mock_get_redis) -> None:
        """Return None on Redis cache miss."""
        mock_client = MagicMock()
        mock_client.get.return_value = None
        mock_get_redis.return_value = mock_client

        result = self.service._get_from_cache("some-key")

        self.assertIsNone(result)

    @patch("services.NewsService.get_redis_client")
    def test_get_from_cache_redis_error(self, mock_get_redis) -> None:
        """Gracefully fall back to None when Redis get fails."""
        mock_client = MagicMock()
        mock_client.get.side_effect = Exception("redis timeout")
        mock_get_redis.return_value = mock_client

        result = self.service._get_from_cache("some-key")

        self.assertIsNone(result)

    @patch("services.NewsService.get_redis_client")
    def test_set_cache_success(self, mock_get_redis) -> None:
        """Store non-empty payload in Redis with configured TTL."""
        mock_client = MagicMock()
        mock_get_redis.return_value = mock_client

        data = [{"title": "Sample", "source": "S", "date": "01/01/2026", "url": "u"}]
        self.service._set_cache("some-key", data)

        mock_client.setex.assert_called_once()
        setex_args = mock_client.setex.call_args[0]
        self.assertEqual(setex_args[0], "some-key")
        self.assertEqual(setex_args[1], 3600)
        self.assertEqual(json.loads(setex_args[2]), data)

    @patch("services.NewsService.get_redis_client")
    def test_set_cache_skips_empty_data(self, mock_get_redis) -> None:
        """Skip cache writes when result payload is empty."""
        mock_client = MagicMock()
        mock_get_redis.return_value = mock_client

        self.service._set_cache("some-key", [])

        mock_client.setex.assert_not_called()

    @patch("services.NewsService.get_redis_client")
    def test_get_news_cache_hit_skips_db_and_llm(self, mock_get_redis) -> None:
        """Short-circuit getNews on cache hit without DB/LLM calls."""
        cached_data = [{"title": "Cached", "source": "S", "date": "01/01/2026", "url": "u"}]
        mock_client = MagicMock()
        mock_client.get.return_value = json.dumps(cached_data)
        mock_get_redis.return_value = mock_client

        result = self.service.getNews(user_keywords="firewall", llm=True)

        self.assertEqual(result, cached_data)
        self.service.db.get_news_collections.assert_not_called()

    @patch("services.NewsService.LLMChain")
    @patch("services.NewsService.get_redis_client")
    def test_get_news_cache_miss_calls_db_llm_and_caches(
        self, mock_get_redis, mock_llm_chain
    ) -> None:
        """On cache miss, getNews should query DB, call LLM, and write cache."""
        mock_client = MagicMock()
        mock_client.get.return_value = None
        mock_get_redis.return_value = mock_client

        self.service.db.get_news_collections.return_value = [
            {
                "headlines": "Sample",
                "author": "Source",
                "newsDate": "01/01/2026",
                "newsURL": "https://example.com",
            }
        ]
        self.service.llm = MagicMock()
        self.service.load_json_file = MagicMock(
            return_value=[
                {
                    "role": "user",
                    "content": "<news_data_placeholder> <user_keywords_placeholder> {news_format} {news_number}",
                }
            ]
        )

        llm_chain_instance = MagicMock()
        llm_chain_instance.invoke.return_value = {
            "text": "\n[Title, Source, 01/01/2026, https://example.com]"
        }
        mock_llm_chain.return_value = llm_chain_instance

        with patch.object(
            self.service,
            "toJSON",
            return_value=[
                {
                    "title": "Title",
                    "source": "Source",
                    "date": "01/01/2026",
                    "url": "https://example.com",
                }
            ],
        ):
            result = self.service.getNews(user_keywords="firewall", llm=True)

        self.assertEqual(len(result), 1)
        self.service.db.get_news_collections.assert_called_once_with(
            is_keyword=True, keyword="firewall"
        )
        llm_chain_instance.invoke.assert_called_once()
        mock_client.setex.assert_called_once()

    @patch("services.NewsService.LLMChain")
    @patch("services.NewsService.get_redis_client", return_value=None)
    def test_get_news_redis_unavailable_still_returns_result(
        self, _mock_get_redis, mock_llm_chain
    ) -> None:
        """If Redis is unavailable, getNews should still complete using DB+LLM."""
        self.service.db.get_news_collections.return_value = [
            {
                "headlines": "Sample",
                "author": "Source",
                "newsDate": "01/01/2026",
                "newsURL": "https://example.com",
            }
        ]
        self.service.llm = MagicMock()
        self.service.load_json_file = MagicMock(
            return_value=[
                {
                    "role": "user",
                    "content": "<news_data_placeholder> <user_keywords_placeholder> {news_format} {news_number}",
                }
            ]
        )

        llm_chain_instance = MagicMock()
        llm_chain_instance.invoke.return_value = {
            "text": "\n[Title, Source, 01/01/2026, https://example.com]"
        }
        mock_llm_chain.return_value = llm_chain_instance

        expected = [
            {
                "title": "Title",
                "source": "Source",
                "date": "01/01/2026",
                "url": "https://example.com",
            }
        ]
        with patch.object(self.service, "toJSON", return_value=expected):
            result = self.service.getNews(user_keywords="firewall", llm=True)

        self.assertEqual(result, expected)
        self.service.db.get_news_collections.assert_called_once_with(
            is_keyword=True, keyword="firewall"
        )
        llm_chain_instance.invoke.assert_called_once()


if __name__ == "__main__":
    unittest.main()
