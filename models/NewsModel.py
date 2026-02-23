from config.Database import client
import logging

logger = logging.getLogger(__name__)

class CybernewsDB:
    def __init__(self):
        self.client = client
        self.index_name = "cybernews-index"
        self.namespace = "c2si"
        self.index = None
        
        # Only try to access index if client is available
        if self.client is not None:
            try:
                self.index = self.client.Index(self.index_name)
                logger.info("✓ Pinecone index connected")
            except Exception as e:
                logger.warning(f"⚠ Could not connect to Pinecone index: {e}")
                self.index = None
        else:
            logger.warning("⚠ Pinecone client not initialized (missing/invalid API key)")
        
        # Import CacheService here to avoid circular imports
        from services.CacheService import CacheService
        self.cache = CacheService()

    def is_available(self):
        """Check if database is available"""
        return self.client is not None and self.index is not None

    def extract_metadata(self , nested_dict):
        """
        Extracts the 'metadata' dictionaries from a nested dictionary structure.

        Parameters:
        nested_dict (dict): The input dictionary with IDs as keys and dictionaries as values.

        Returns:
        list: A list containing all the extracted 'metadata' dictionaries.
        """
        metadata_list = []

        for key, value in nested_dict.items():
            if isinstance(value, dict) and 'metadata' in value:
                metadata = value['metadata']
                if isinstance(metadata, dict):
                    metadata_list.append(metadata)

        return metadata_list
    

    def fetch_all_from_namespace(self, batch_size=100):
        """Fetch all vectors from Pinecone with error handling"""
        if not self.is_available():
            logger.warning("⚠ Cannot fetch: Pinecone not available")
            return []
        
        try:
            start_cursor = None
            final_list = []
            id_list = []
            while True:
                response = self.index.query(
                    vector=[0]*384,  
                    namespace=self.namespace,
                    top_k=batch_size,
                    include_metadata=False,
                    include_values=False,
                    cursor=start_cursor
                )
                ids = [match['id'] for match in response['matches']]
                id_list.extend(ids)
                start_cursor = response.get('next_cursor')
                if not start_cursor:
                    break

            # Fetch the vectors using the retrieved IDs
            for i in range(0, len(id_list), batch_size):
                batch_ids = id_list[i:i + batch_size]
                response = self.index.fetch(ids=batch_ids, namespace=self.namespace)
                vectors = response.get('vectors', [])
                key_list = vectors.keys()
                key_list = list(key_list)

                for i in key_list:
                    metadata_dict = vectors[i].get('metadata', {})  
                    final_list.append(metadata_dict)  

            return final_list
        except Exception as e:
            logger.error(f"⚠ Error fetching from Pinecone: {e}")
            return []

    def get_news_collections(self):
        """
        Fetch all news collections with caching.
        First checks Redis cache, falls back to Pinecone if not cached.
        Returns empty list if database unavailable.
        """
        cache_key = "news:collections:all"
        
        # Try to get from cache first
        cached_data = self.cache.get(cache_key)
        if cached_data is not None:
            logger.info("✓ News collections retrieved from cache")
            return cached_data
        
        # If not in cache, fetch from Pinecone (with error handling)
        if not self.is_available():
            logger.warning("⚠ Database unavailable. Returning empty news list.")
            return []
        
        logger.info("Fetching news collections from Pinecone...")
        news_data = self.fetch_all_from_namespace()
        
        # Cache the result
        if news_data:
            self.cache.set(cache_key, news_data)
            logger.info(f"✓ Cached {len(news_data)} news items")
        
        return news_data
    
    def invalidate_news_cache(self):
        """
        Invalidate all news-related cache entries.
        Call this when new news is added via Update.py
        """
        deleted = self.cache.invalidate_pattern("news:*")
        logger.info(f"Invalidated {deleted} cache entries")
