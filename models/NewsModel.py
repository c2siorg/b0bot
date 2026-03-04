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
    def get_news_collections(self):
        return self.fetch_all_from_namespace()
