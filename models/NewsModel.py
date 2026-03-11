from typing import List, Optional
from pydantic import BaseModel, Field
from config.Database import client

# ==========================================
# 1. THE SCHEMA (The "Modernization" Layer)
# ==========================================
class NewsArticle(BaseModel):
    """
    Data Transfer Object (DTO) for Cybersecurity News.
    Ensures LLM output is structured and validated via Pydantic v2.
    """
    title: str = Field(..., description="The headline of the news article")
    summary: str = Field(..., description="A brief AI-generated summary of the content")
    url: str = Field(..., description="The source URL of the article")
    timestamp: Optional[str] = Field(None, description="The publication date if available")

class NewsResponse(BaseModel):
    """Wrapper for multiple news articles to ensure list-level validation."""
    articles: List[NewsArticle]

# ==========================================
# 2. THE DATABASE LOGIC (The "Data Access" Layer)
# ==========================================
class CybernewsDB:
    """
    Data Access Object (DAO) for interacting with Pinecone Vector Database.
    """
    def __init__(self):
        self.client = client
        self.index_name = "cybernews-index"
        self.namespace = "c2si" 
        self.index = self.client.Index(self.index_name)

    def extract_metadata(self, nested_dict: dict) -> List[dict]:
        """
        Extracts the 'metadata' dictionaries from a nested Pinecone structure.
        """
        metadata_list = []
        for key, value in nested_dict.items():
            if isinstance(value, dict) and 'metadata' in value:
                metadata = value['metadata']
                if isinstance(metadata, dict):
                    metadata_list.append(metadata)
        return metadata_list

    def fetch_all_from_namespace(self, batch_size: int = 100) -> List[dict]:
        """
        Retrieves all vector metadata from the specified namespace.
        Uses a zero-vector query to trigger a full-index scan (brute-force fetch).
        """
        start_cursor = None
        id_list = []
        final_list = []

        # Step 1: Fetch all vector IDs
        while True:
            response = self.index.query(
                vector=[0]*384, # Matches the embedding dimension of common models (e.g., all-MiniLM-L6-v2)
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

        # Step 2: Fetch metadata using the retrieved IDs in batches
        for i in range(0, len(id_list), batch_size):
            batch_ids = id_list[i:i + batch_size]
            response = self.index.fetch(ids=batch_ids, namespace=self.namespace)
            vectors = response.get('vectors', {})
            
            for vector_id in vectors:
                metadata_dict = vectors[vector_id].get('metadata', {})  
                final_list.append(metadata_dict)  

        return final_list

    def get_news_collections(self) -> List[dict]:
        """Entry point for retrieving the raw news data for the LLM context."""
        return self.fetch_all_from_namespace()
