from dotenv import dotenv_values
from pinecone import Pinecone
import os
import sys
import redis
import numpy as np
import pickle
import logging

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

PINECONE_API = dotenv_values(".env").get("PINECONE_API_KEY")

client = Pinecone(api_key=PINECONE_API)
index_name = "cybernews-index"

class SemanticCache:
    def __init__(self, redis_client=None, model=None, threshold=0.92, ttl=3600):
        self.redis = redis_client
        self.model = model
        self.threshold = threshold
        self.ttl = ttl
        self.logger = logging.getLogger(__name__)
        self.hits = 0
        self.misses = 0

    def _cosine_similarity(self, v1, v2):
        return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

    def get(self, query):
        if not self.redis or not self.model:
            return None
        try:
            query_embedding = self.model.encode(query)
            keys = self.redis.keys("cache:*")
            
            best_match = None
            max_similarity = -1

            for key in keys:
                raw_data = self.redis.get(key)
                if not raw_data:
                    continue
                cached_data = pickle.loads(raw_data)
                similarity = self._cosine_similarity(query_embedding, cached_data['embedding'])
                
                if similarity > max_similarity:
                    max_similarity = similarity
                    best_match = cached_data['response']

            if max_similarity >= self.threshold:
                self.logger.info(f"Semantic cache hit! Similarity: {max_similarity:.4f}")
                self.hits += 1
                return best_match
            
            self.misses += 1
            return None
        except Exception as e:
            self.logger.warning(f"Semantic cache error during get: {e}")
            return None

    def set(self, query, response):
        if not self.redis or not self.model:
            return
        try:
            query_embedding = self.model.encode(query)
            # Use query itself or hash as part of key
            cache_key = f"cache:{hash(query)}"
            data = {
                'embedding': query_embedding,
                'response': response
            }
            self.redis.setex(cache_key, self.ttl, pickle.dumps(data))
        except Exception as e:
            self.logger.warning(f"Semantic cache error during set: {e}")

    def get_stats(self):
        total = self.hits + self.misses
        return {
            "hits": self.hits,
            "misses": self.misses,
            "total_queries": total,
            "hit_rate": (self.hits / total) if total > 0 else 0,
            "cached_items": len(self.redis.keys("cache:*")) if self.redis else 0
        }