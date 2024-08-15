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
    

    def fetch_all_from_namespace(self, batch_size=100):
        all_vectors = []
        start_cursor = None
        final_list = []
        # Fetch all vector IDs first
        id_list = []
        while True:
            # Replace `query` with appropriate method to retrieve IDs if needed
            response = self.index.query(
                vector=[0]*384,  # Assuming 512 dimensions; replace with actual dimension
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
            # print(type(response))
            vectors = response.get('vectors', [])
            key_list = vectors.keys()
            key_list = list(key_list)

            for i in key_list:
                metadata_dict = vectors[i].get('metadata', {})  # Extract the metadata dictionary
                final_list.append(metadata_dict)  # Append the entire metadata dictionary to the list

        # print(final_list)

        return final_list

    def get_news_collections(self):
        return self.fetch_all_from_namespace()
