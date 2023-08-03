from config.Database import client

"""
TODO: Read news from database.
"""


class CybernewsDB:
    def __init__(self):
        self.client = client
        self.db = self.client["CybernewsDB"]

    def get_collections(self, collection_name):
        return self.db.get_collection(collection_name)
