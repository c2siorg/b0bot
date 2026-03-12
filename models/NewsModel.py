from config.Database import client

class CybernewsDB:
    def __init__(self):
        self.client = client
        self.index_name = "cybernews-index"
        self.namespace = "c2si"
        self.index = self.client.Index(self.index_name)

    def fetch_all_from_namespace(self, limit=100, min_date=None):
        """
        Returns a bounded subset of news metadata from the namespace.

        Uses a single Pinecone query with include_metadata=True to avoid the
        previous two-pass approach (full ID scan + batch fetch) that caused
        unbounded read volume as the index grew.

        Args:
            limit:    Maximum number of results to return (default 100).
            min_date: Optional ISO date string; when provided, only records
                      with newsDate >= min_date are returned.
        """
        filter_params = {"newsDate": {"$gte": min_date}} if min_date else None

        response = self.index.query(
            vector=[0] * 384,
            namespace=self.namespace,
            top_k=limit,
            include_metadata=True,
            include_values=False,
            filter=filter_params,
        )

        return [
            match["metadata"]
            for match in response.get("matches", [])
            if match.get("metadata")
        ]

    def get_news_collections(self, limit=100):
        return self.fetch_all_from_namespace(limit=limit)
