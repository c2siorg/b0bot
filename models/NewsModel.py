from config.Database import client
from sentence_transformers import SentenceTransformer
from datetime import datetime

class CybernewsDB:
    def __init__(self):
        self.client = client
        self.index_name = "cybernews-index"
        self.namespace = "c2si" 
        self.index = self.client.Index(self.index_name)
        self.model = SentenceTransformer('all-MiniLM-L6-v2')

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
        start_cursor = None
        final_list = []
        # Fetch all vector IDs first
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

    def fetch_keyword_from_namespace(self, keyword):
        if not keyword:
            return []
        vector = self.model.encode(keyword).tolist()

        response = self.index.query(
            vector=vector,
            namespace=self.namespace,
            top_k=50,
            include_metadata=False,
            include_values=False
        )
        id_list = [match['id'] for match in response['matches']]

        if not id_list:
            return []

        final_list = []
        batch_size = 100 
        for i in range(0, len(id_list), batch_size):
            batch_ids = id_list[i:i + batch_size]
            response = self.index.fetch(ids=batch_ids, namespace=self.namespace)
            vectors = response.get('vectors', {})
            
            for vid in batch_ids:
                if vid in vectors:
                    metadata = vectors[vid].get('metadata', {})
                    final_list.append(metadata)

        def parse_date(date_str):
            try:
                return datetime.strptime(str(date_str), '%d/%m/%Y')
            except (ValueError, TypeError):
                return datetime.min

        final_list.sort(key=lambda x: parse_date(x.get('newsDate')), reverse=True)

        return final_list

    def get_news_collections(self, is_keyword=False, keyword=None):
        if is_keyword and keyword:
            return self.fetch_keyword_from_namespace(keyword)
        else:
            return self.fetch_all_from_namespace()


if __name__ == "__main__":
    db = CybernewsDB()
    print(db.get_news_collections(is_keyword=True, keyword="AI"))