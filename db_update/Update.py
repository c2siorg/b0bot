import sys
import os
import uuid
import time
from datetime import datetime
from dotenv import dotenv_values
import feedparser

from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer


# ---------------------------
# RSS Cybersecurity Feeds
# ---------------------------

FEEDS = {
    "general_news": "https://feeds.feedburner.com/TheHackersNews",
    "cyber_attack_news": "https://www.bleepingcomputer.com/feed/",
    "security_news": "https://www.darkreading.com/rss.xml",
    "vulnerability_news": "https://krebsonsecurity.com/feed/"
}


# ---------------------------
# Feed Parsing
# ---------------------------

def parse_feed(url):
    feed = feedparser.parse(url)
    articles = []

    for entry in feed.entries:
        articles.append({
            "id": str(uuid.uuid4()),
            "headlines": entry.title,
            "author": entry.get("author", "Unknown"),
            "fullNews": entry.get("summary", ""),
            "newsURL": entry.link,
            "newsImgURL": "",
            "newsDate": entry.get("published", str(datetime.now()))
        })

    return articles


def get_all_news():
    newsBox = {}
    for category, url in FEEDS.items():
        newsBox[category] = parse_feed(url)
    return newsBox


# ---------------------------
# Main Execution Logic
# ---------------------------

def main():

    # ---------------------------
    # Pinecone Configuration
    # ---------------------------

    PINECONE_API = dotenv_values(".env").get("PINECONE_API_KEY")

    pc = Pinecone(api_key=PINECONE_API)
    index_name = "cybernews-index"
    namespace = "c2si"

    # Delete index if exists (optional behavior retained)
    if index_name in pc.list_indexes().names():
        pc.delete_index(index_name)
        print(f"Deleted existing index: {index_name}")

    # Create index if not exists
    if index_name not in pc.list_indexes().names():
        pc.create_index(
            name=index_name,
            dimension=384,
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1"
            )
        )

        while True:
            description = pc.describe_index(index_name)
            if description.status['ready']:
                break
            time.sleep(2)

        print("Index is ready.")

    index = pc.Index(index_name)

    # ---------------------------
    # Embedding Model
    # ---------------------------

    model = SentenceTransformer("all-MiniLM-L6-v2")

    # ---------------------------
    # Fetch News
    # ---------------------------

    newsBox = get_all_news()

    # ---------------------------
    # Embed & Store
    # ---------------------------

    for news_type, articles in newsBox.items():
        print(f"\nProcessing category: {news_type}")

        for article in articles:
            text = article["headlines"] + " " + article["fullNews"]

            vector = model.encode(text).tolist()
            document_id = article["id"]

            metadata = {
                "category": news_type,
                "headlines": article["headlines"],
                "author": article["author"],
                "fullNews": article["fullNews"],
                "newsURL": article["newsURL"],
                "newsImgURL": article["newsImgURL"],
                "newsDate": article["newsDate"]
            }

            index.upsert(
                [(document_id, vector, metadata)],
                namespace=namespace
            )

            print(f"Inserted article ID: {document_id}")

    print("\nAll news articles processed successfully.")

    stats = index.describe_index_stats()
    print("Vector count:", stats['total_vector_count'])


# ---------------------------
# Prevent Auto Execution on Import
# ---------------------------

if __name__ == "__main__":
    main()