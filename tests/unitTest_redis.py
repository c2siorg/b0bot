import unittest
import hashlib
import redis
from unittest.mock import patch, MagicMock
from flask import Flask
from config.Redis import redis_client
from routes.NewsRoutes import get_cache_key

class TestRedisCache(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = Flask(__name__)
        cls.app.config["TESTING"] = True
        cls.client = cls.app.test_client()

    def setUp(self):
        redis_client.flushdb()  

    def tearDown(self):
        redis_client.flushdb()  

    def test_redis_connection(self):
        try:
            redis_client.ping()
            connected = True
        except redis.ConnectionError:
            connected = False
        self.assertTrue(connected, "Redis is not connected")

    def test_cache_storage(self):
        test_key = "test_key"
        test_value = "test_value"
        
        redis_client.set(test_key, test_value, ex=10)  
        cached_value = redis_client.get(test_key)
        
        self.assertIsNotNone(cached_value, "Failed to store value in Redis")
        self.assertEqual(cached_value.decode(), test_value, "Retrieved incorrect value from Redis")

    def test_cache_expiry(self):
        test_key = "temp_key"
        redis_client.set(test_key, "temp_value", ex=1)  
        
        import time
        time.sleep(2)  
        
        cached_value = redis_client.get(test_key)
        self.assertIsNone(cached_value, "Cache expiration did not work")

    def test_cache_key_generation(self):
        key = get_cache_key("news", "mistralai", ["AI", "ML"])
        
        expected_key = "news:news:mistralai:" + hashlib.md5("AI,ML".encode()).hexdigest()
        self.assertEqual(key, expected_key, "Cache key generation is incorrect")

    @patch("redis.Redis")
    def test_mocked_redis(self, mock_redis):
        mock_instance = mock_redis.return_value
        mock_instance.get.return_value = b"mocked_value"

        redis_client.set("mock_key", "mocked_value")
        value = redis_client.get("mock_key").decode()

        self.assertEqual(value, "mocked_value", "Mocked Redis did not return expected value")

if __name__ == "__main__":
    unittest.main()
