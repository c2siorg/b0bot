from config.Database import client

class CybernewsDB:
    def __init__(self):
        self.client = client
        self.index_name = "cybernews-index"
        self.namespace = "c2si" 
        self.index = self.client.Index(self.index_name)

    def fetch_all_from_namespace(self, batch_size=100):
        # pinecone.init(api_key=api_key)
        index = client.Index(self.index_name)
        all_vectors = []
        start_cursor = None

        while True:
            response = index.fetch(limit=batch_size, cursor=start_cursor, include_metadata=True, namespace=self.namespace)
            vectors = response.get('vectors', [])

            if not vectors:
                break

            all_vectors.extend(vectors)
            start_cursor = response.get('next_cursor')

            if not start_cursor:
                break

        return all_vectors

    def get_news_collections(self):
        return self.fetch_all_from_namespace(self.index_name, self.namespace)
