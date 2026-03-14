import sys
import os
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------
load_dotenv()
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from cybernews.CyberNews import CyberNews

# ---------------------------------------------------------------------------
# News categories — each key maps to the CyberNews query string.
# Every category is independent, so they can be fetched in parallel.
# ---------------------------------------------------------------------------
CATEGORIES = {
    "general_news":       "general",
    "cyber_attack_news":  "cyberAttack",
    "vulnerability_news": "vulnerability",
    "malware_news":       "malware",
    "security_news":      "security",
    "data_breach_news":   "dataBreach",
}


def _fetch_category(category_key, category_query, news_client):
    """Fetch a single news category.  Thread-safe because each call
    creates its own HTTP sessions inside CyberNews."""
    articles = news_client.get_news(category_query)
    logger.info("Fetched %d articles for [%s]", len(articles), category_key)
    return category_key, articles


# ---------------------------------------------------------------------------
# Pinecone setup
# ---------------------------------------------------------------------------
PINECONE_API = os.environ.get("PINECONE_API_KEY")

pc = Pinecone(api_key=PINECONE_API)
index_name = "cybernews-index"

# Delete the index if it already exists, so as to save storage
if index_name in pc.list_indexes().names():
    pc.delete_index(index_name)
    logger.info("Deleted existing index: %s", index_name)

# Create the index if it does not exist
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

index = pc.Index(index_name)

namespace = "c2si"

model = SentenceTransformer('all-MiniLM-L6-v2')

# ---------------------------------------------------------------------------
# Fetch all news categories concurrently  (fixes #100)
# ---------------------------------------------------------------------------
news = CyberNews()
newsBox = {}

with ThreadPoolExecutor(max_workers=len(CATEGORIES)) as pool:
    futures = {
        pool.submit(_fetch_category, key, query, news): key
        for key, query in CATEGORIES.items()
    }
    for future in as_completed(futures):
        cat = futures[future]
        try:
            key, articles = future.result()
            newsBox[key] = articles
        except Exception:
            logger.exception("Failed to fetch category '%s' — skipping", cat)

logger.info(
    "Scraping complete: %d categories, %d total articles",
    len(newsBox),
    sum(len(v) for v in newsBox.values()),
)

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

Notice: "id" should be removed before the news is inserted into the database.
        newsImgURL also not important right now.
"""

# ---------------------------------------------------------------------------
# Convert news articles to vectors and upsert into Pinecone
# ---------------------------------------------------------------------------
for news_type, articles in newsBox.items():
    for article in articles:
        text = article["headlines"] + " " + article["fullNews"]

        vector = model.encode(text).tolist()

        document_id = str(article["id"])

        metadata = {
            "headlines": article["headlines"],
            "author": article["author"],
            "fullNews": article["fullNews"],
            "newsURL": article["newsURL"],
            "newsImgURL": article["newsImgURL"],
            "newsDate": article["newsDate"],
        }

        index.upsert([(document_id, vector, metadata)], namespace=namespace)

        logger.info(
            "Inserted article ID: %s into index: %s", document_id, index_name
        )

