from config.Database import client

class CybernewsDB:
    def __init__(self):
        self.client = client
        self.index_name = "cybernews-index"
        self.namespace = "c2si" 
        self.index = self.client.Index(self.index_name)

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
    

    def fetch_all_from_namespace(self, top_k=50):
        """
<<<<<<< HEAD
    Fetch recent news from Pinecone using metadata filtering
    instead of full index scan for better performance.
    """
        response = self.index.query(
        vector=[0]*384,
        namespace=self.namespace,
        top_k=top_k,
        include_metadata=True,
        include_values=False
    )
    
        return [
        match['metadata'] 
        for match in response['matches']
        if match.get('metadata')
    ]
=======
        Fetch recent news from Pinecone using a single metadata-filtered query
        instead of full index scan for better performance.
        Reduces from N+1 API calls to a single API call regardless of index size.
        """
        response = self.index.query(
            vector=[0]*384,
            namespace=self.namespace,
            top_k=top_k,
            include_metadata=True,
            include_values=False,
            filter={"newsDate": {"$exists": True}}
        )
        
        return [
            match['metadata'] 
            for match in response['matches']
            if match.get('metadata')
        ]

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

>>>>>>> 4a53197 (fix: add newsDate metadata filter to further optimize Pinecone query)
    def get_news_collections(self):
        return self.fetch_all_from_namespace()
