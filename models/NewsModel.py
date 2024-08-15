from config.Database import client

class CybernewsDB:
    def __init__(self):
        self.client = client
        self.index_name = "cybernews-index"
        self.namespace = "c2si" 
        self.index = self.client.Index(self.index_name)

    def fetch_all_from_namespace(self, batch_size=100):
        all_vectors = []
        start_cursor = None

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
            vectors = response.get('vectors', [])
            all_vectors.extend(vectors)

        return all_vectors

    def get_news_collections(self):
        return self.fetch_all_from_namespace()
