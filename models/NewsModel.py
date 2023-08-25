from config.Database import client


class CybernewsDB:
    def __init__(self):
        self.client = client
        self.db = self.client["CybernewsDB"]

    def get_news_collections(self):
        return self.db.get_collection("news")
