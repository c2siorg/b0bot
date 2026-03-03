import unittest
import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.redis_config import get_cache, set_cache

class SimpleRedisTest(unittest.TestCase):
    """Simple test cases for Redis caching functionality in B0Bot"""

    def test_redis_set_get(self):
        """Test basic set and get operations with Redis cache"""
        test_key = "test:simple:key"
        test_data = {
            "title": "Test News Article",
            "source": "Test Source",
            "date": "01/01/2025",
            "url": "https://example.com/test"
        }
        
        test_json = json.dumps(test_data)
        
        set_result = set_cache(test_key, test_json)
        self.assertTrue(set_result, "Failed to set data in Redis cache")
        
        cached_data = get_cache(test_key)
        self.assertIsNotNone(cached_data, "Failed to retrieve data from Redis cache")
        
        retrieved_data = json.loads(cached_data)
        self.assertEqual(retrieved_data, test_data, "Retrieved data does not match original data")
        
        missing_data = get_cache("nonexistent:key")
        self.assertIsNone(missing_data, "Should return None for non-existent key")

if __name__ == '__main__':
    unittest.main()