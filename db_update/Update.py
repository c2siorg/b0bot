import sys
import os
import logging
import time
from dotenv import dotenv_values
from pinecone import Pinecone , ServerlessSpec
from sentence_transformers import SentenceTransformer
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from cybernews.CyberNews import CyberNews

logger = logging.getLogger(__name__)
if not logging.getLogger().handlers:
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")


PINECONE_API = dotenv_values(".env").get("PINECONE_API_KEY")

# configure client
pc = Pinecone(api_key=PINECONE_API)
index_name = "cybernews-index"

# Delete the index if it already exists, so as to save storage
if index_name in pc.list_indexes().names():
    pc.delete_index(index_name)
    print(f"Deleted existing index: {index_name}")

# Create or access the index
if index_name not in pc.list_indexes():
    pc.create_index(
        name=index_name, 
        dimension=384, 
        metric='cosine',
        spec=ServerlessSpec(
            cloud='aws',
            region='us-east-1'
        )
    )

# Connect to the index
index = pc.Index(index_name)

namespace = "c2si"

model = SentenceTransformer('all-MiniLM-L6-v2')

# Different types of news
news = CyberNews()

newsBox = dict()

_sources = [
    ("general_news", "general"),
    ("cyber_attack_news", "cyberAttack"),
    ("vulnerability_news", "vulnerability"),
    ("malware_news", "malware"),
    ("security_news", "security"),
    ("data_breach_news", "dataBreach"),
]
for key, news_type in _sources:
    try:
        newsBox[key] = news.get_news(news_type)
    except Exception as e:
        logger.warning("Skipping source %s after failure: %s", key, e)
        newsBox[key] = []   


"""
News Format:

news = {
    "id: ""
    "headlines": "",
    "author": "",
    "fullNews": "",
    "newsURL": "",
    "newsImgURL":
    "newsDate": "",
}

Notice: "id" should be removed before the news is inserted into the database. newsImgURL also not important right now.
"""

def _upsert_article(index, namespace, document_id, vector, metadata, index_name, max_retries=2):
    for attempt in range(max_retries):
        try:
            index.upsert([(document_id, vector, metadata)], namespace=namespace)
            print(f"Inserted article ID: {document_id} with metadata into index: {index_name}")
            return
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(1)
            else:
                raise

for news_type, articles in newsBox.items():
    for article in articles:
        try:
            text = article["headlines"] + " " + article["fullNews"]
            vector = model.encode(text).tolist()
            document_id = str(article["id"])
            metadata = {
                "headlines": article["headlines"],
                "author": article["author"],
                "fullNews": article["fullNews"],
                "newsURL": article["newsURL"],
                "newsImgURL": article["newsImgURL"],
                "newsDate": article["newsDate"]
            }
            _upsert_article(index, namespace, document_id, vector, metadata, index_name)
        except Exception as e:
            logger.warning("Skipping article %s (%s): %s", article.get("id"), news_type, e)

