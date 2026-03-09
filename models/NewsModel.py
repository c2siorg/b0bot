from config.Database import client

class CybernewsDB:
    def __init__(self):
        self.client = client
        self.index_name = "cybernews-index"
        self.namespace = "c2si"
        self.index = self.client.Index(self.index_name)

    def extract_metadata(self, nested_dict):
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
        id_list = []

        # Fetch all vector IDs first
        while True:
            response = self.index.query(
                vector=[0] * 384,
                namespace=self.namespace,
                top_k=batch_size,
                include_metadata=False,
                include_values=False,
                cursor=start_cursor
            )
            ids = [match['id'] for match in response['matches']]
            id_list.extend(ids)
            start_cursor = getattr(response, 'next_cursor', None)
            if not start_cursor:
                break

        # Fetch the vectors using the retrieved IDs
        for i in range(0, len(id_list), batch_size):
            batch_ids = id_list[i:i + batch_size]
            response = self.index.fetch(ids=batch_ids, namespace=self.namespace)

            # Access the 'vectors' safely
            vectors = getattr(response, 'vectors', {})

            for key, vector in vectors.items():
                metadata_dict = getattr(vector, 'metadata', {})
                final_list.append(metadata_dict)

        return final_list

    def get_news_collections(self):
        return self.fetch_all_from_namespace()
