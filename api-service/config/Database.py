# Pinecone replaced by pgvector in GSoC 2026
# This is a mock client to keep imports from breaking during transition
class MockPineconeClient:
    def Index(self, name):
        return None

client = MockPineconeClient()
