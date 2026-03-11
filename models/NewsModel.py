from config.Database import client
from datetime import datetime

class CybernewsDB:
    def __init__(self):
        self.client = client
        self.index_name = "cybernews-hybrid-test"
        self.namespace = "c2si" 
        self.index = self.client.Index(self.index_name)

    @staticmethod
    def parse_date(date_str):
        if not date_str or str(date_str).strip() == "":
            return datetime.min
        
        # Try formats: 'DD/MM/YYYY' or 'Month DD, YYYY'
        for fmt in ('%d/%m/%Y', '%b %d, %Y'):
            try:
                return datetime.strptime(str(date_str), fmt)
            except (ValueError, TypeError):
                continue
        return datetime.min

    def extract_metadata(self, nested_dict):
        metadata_list = []
        for key, value in nested_dict.items():
            if isinstance(value, dict) and 'metadata' in value:
                metadata = value['metadata']
                if isinstance(metadata, dict):
                    metadata_list.append(metadata)
        return metadata_list

    def fetch_all_from_namespace(self, batch_size=100):
        final_list = []
        
        # Use list() generator to get all IDs page by page
        for ids_page in self.index.list(namespace=self.namespace):
            if not ids_page:
                continue
                
            # Fetch metadata in batches for each page of IDs
            for i in range(0, len(ids_page), batch_size):
                batch_ids = ids_page[i:i + batch_size]
                response = self.index.fetch(ids=batch_ids, namespace=self.namespace)
                
                vectors = response.vectors
                for vid in batch_ids:
                    if vid in vectors:
                        final_list.append(vectors[vid].metadata)
        
        final_list.sort(key=lambda x: CybernewsDB.parse_date(x.get('newsDate')), reverse=True)
        return final_list

    def fetch_keyword_from_namespace(self, keyword, alpha=0.5):
        if not keyword:
            return []

        # 1. Generate Dense Vector using Pinecone Inference
        dense_query_embedding = self.client.inference.embed(
            model="llama-text-embed-v2",
            inputs=[keyword],
            parameters={"dimension": 384, "input_type": "query", "truncate": "END"}
        )
        
        # 2. Generate Sparse Vector using Pinecone Inference
        sparse_query_embedding = self.client.inference.embed(
            model="pinecone-sparse-english-v0",
            inputs=[keyword],
            parameters={"input_type": "query", "truncate": "END"}
        )

        # 3. Execute Hybrid Query 
        final_list = []
        for d, s in zip(dense_query_embedding, sparse_query_embedding):
            # Apply alpha weighting
            scaled_dense = [v * alpha for v in d['values']]
            scaled_sparse = {
                "indices": s['sparse_indices'],
                "values": [v * (1 - alpha) for v in s['sparse_values']]
            }

            response = self.index.query(
                namespace=self.namespace,
                top_k=50,
                vector=scaled_dense,
                sparse_vector=scaled_sparse,
                include_metadata=True,
                include_values=False
            )
            
            # Map doc to metadata format
            for match in response.matches:
                metadata = match.metadata
                # Add score for reference if needed
                metadata['_score'] = match.score
                final_list.append(metadata)

        if not final_list:
            return []

        final_list.sort(key=lambda x: (x.get('_score', 0), CybernewsDB.parse_date(x.get('newsDate'))), reverse=True)
        return final_list

    def fetch_lexical_from_namespace(self, keyword):
        if not keyword:
            return []

        # 1. Generate Sparse Vector using Pinecone Inference
        sparse_query_embedding = self.client.inference.embed(
            model="pinecone-sparse-english-v0",
            inputs=[keyword],
            parameters={"input_type": "query", "truncate": "END"}
        )

        # 2. Execute Lexical Query (Provide dummy zero vector to satisfy Pinecone requirement)
        final_list = []
        dummy_dense = [0.0] * 384 # Match your index dimension
        
        for s in sparse_query_embedding:
            response = self.index.query(
                namespace=self.namespace,
                top_k=50,
                vector=dummy_dense, # Satisfy "dense vector required" rule
                sparse_vector={
                    "indices": s['sparse_indices'], 
                    "values": s['sparse_values']
                },
                include_metadata=True,
                include_values=False
            )
            
            for match in response.matches:
                metadata = match.metadata
                metadata['_score'] = match.score
                final_list.append(metadata)

        if not final_list:
            return []

        final_list.sort(key=lambda x: (x.get('_score', 0), CybernewsDB.parse_date(x.get('newsDate'))), reverse=True)
        return final_list

    def get_news_collections(self, is_keyword=False, keyword=None, search_type="hybrid", alpha=0.3):
        if is_keyword and keyword:
            if search_type == "lexical":
                return self.fetch_lexical_from_namespace(keyword)
            return self.fetch_keyword_from_namespace(keyword, alpha=alpha)
        else:
            return self.fetch_all_from_namespace()
