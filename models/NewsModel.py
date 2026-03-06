from pydantic import BaseModel, Field
from typing import List, Optional
from config.Database import client

# --- THE SCHEMA (Added for LangChain Pydantic Parsing) ---
class NewsArticle(BaseModel):
    title: str = Field(description="The title of the news article")
    source: str = Field(description="The source/publisher of the news")
    date: str = Field(description="The publication date")
    url: str = Field(description="The full URL to the news source")

# --- THE DATABASE LOGIC ---
class CybernewsDB:
    def __init__(self):
        self.client = client
        self.index_name = "cybernews-index"
        self.namespace = "c2si" 
        self.index = self.client.Index(self.index_name)

    def extract_metadata(self, nested_dict):
        """
        Extracts the 'metadata' dictionaries from a nested dictionary structure.
        """
        metadata_list = []
        for key, value in nested_dict.items():
            if isinstance(value, dict) and 'metadata' in value:
                metadata = value['metadata']
                if isinstance(metadata, dict):
                    metadata_list.append(metadata)
        return metadata_list

    def fetch_all_from_namespace(self, batch_size=100):
        start_cursor = None
        final_list = []
        id_list = []
        
        # Fetch all vector IDs first
        while True:
            # Note: vector=[0]*384 is a common trick to retrieve all vectors 
            # in Pinecone when using cosine similarity.
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

        # Fetch the vectors/metadata using the retrieved IDs
        for i in range(0, len(id_list), batch_size):
            batch_ids = id_list[i:i + batch_size]
            response = self.index.fetch(ids=batch_ids, namespace=self.namespace)
            vectors = response.get('vectors', {})
            
            for vector_id in vectors:
                metadata_dict = vectors[vector_id].get('metadata', {})  
                final_list.append(metadata_dict)  

        return final_list

    def get_news_collections(self):
        return self.fetch_all_from_namespace()