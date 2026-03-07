from config.Database import client


class CybernewsDB:
    def __init__(self):
        self.client = client
        self.index_name = "cybernews-index"
        self.namespace = "c2si"
        self.index = self.client.Index(self.index_name)

        # Optional debug — remove after confirming
        # print(self.index.describe_index_stats())

    def extract_metadata(self, nested_dict):
        """
        Extracts metadata dictionaries from Pinecone fetch response.
        """
        metadata_list = []

        for key, value in nested_dict.items():
            if isinstance(value, dict) and 'metadata' in value:
                metadata = value['metadata']
                if isinstance(metadata, dict):
                    metadata_list.append(metadata)

        return metadata_list

    def fetch_all_from_namespace(self):
        """
        Properly fetches all vectors from the namespace using
        list() + fetch() instead of query().
        """
        final_list = []

        # List all vector IDs in namespace
        for ids_batch in self.index.list(namespace=self.namespace):
            # Fetch full vector objects using IDs
            response = self.index.fetch(
                ids=ids_batch,
                namespace=self.namespace
            )

            vectors = response.get("vectors", {})

            for vector_id, vector_data in vectors.items():
                metadata = vector_data.get("metadata", {})
                final_list.append(metadata)

        return final_list

    def get_news_collections(self):
        return self.fetch_all_from_namespace()