import sys
import os
import json
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import dotenv_values
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer

from utils.rss_fetcher import RSSFetcher

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from cybernews.CyberNews import CyberNews


# -------- Pinecone Setup --------

PINECONE_API = dotenv_values(".env").get("PINECONE_API_KEY")

pc = Pinecone(api_key=PINECONE_API)
index_name = "cybernews-index"

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

index = pc.Index(index_name)
namespace = "c2si"


# -------- Embedding Model --------

model = SentenceTransformer("all-MiniLM-L6-v2")


# -------- Scraping News (Parallel) --------

news = CyberNews()
newsBox = {}

news_types = {
    "general_news": "general",
    "cyber_attack_news": "cyberAttack",
    "vulnerability_news": "vulnerability",
    "malware_news": "malware",
    "security_news": "security",
    "data_breach_news": "dataBreach"
}


def fetch_news(category_key, category_value):
    try:
        return category_key, news.get_news(category_value)
    except Exception as e:
        print(f"Error fetching {category_key}: {e}")
        return category_key, []


with ThreadPoolExecutor(max_workers=6) as executor:

    futures = [
        executor.submit(fetch_news, key, value)
        for key, value in news_types.items()
    ]

    for future in as_completed(futures):
        key, articles = future.result()
        newsBox[key] = articles


# -------- RSS Integration (Parallel) --------

try:
    with open("config/rss_sources.json") as f:
        rss_sources = json.load(f)

    rss_articles = []

    def fetch_rss(name, url):
        try:
            fetcher = RSSFetcher(url)
            return name, fetcher.fetch(limit=10)
        except Exception as e:
            print(f"RSS fetch failed for {name}: {e}")
            return name, []

    with ThreadPoolExecutor(max_workers=8) as executor:

        futures = [
            executor.submit(fetch_rss, name, url)
            for name, url in rss_sources.items()
        ]

        for future in as_completed(futures):
            name, fetched = future.result()

            for item in fetched:
                url_hash = hashlib.md5(item["url"].encode()).hexdigest()

                rss_articles.append({
                    "id": f"rss_{name}_{url_hash}",
                    "headlines": item["title"],
                    "author": name,
                    "fullNews": item["title"],
                    "newsURL": item["url"],
                    "newsImgURL": "",
                    "newsDate": item["date"]
                })

    newsBox["rss_news"] = rss_articles
    print(f"Added {len(rss_articles)} RSS articles")

except Exception as e:
    print("RSS loading failed:", e)


# -------- Optimized Batched Ingestion --------

existing_ids = set()

texts = []
ids = []
metadata_list = []


# -------- Collect Articles --------

for news_type, articles in newsBox.items():
    for article in articles:

        document_id = str(article["id"])

        if document_id in existing_ids:
            continue

        existing_ids.add(document_id)

        text = f"{article['headlines']}. {article['fullNews']}"

        metadata = {
            "headlines": article["headlines"],
            "author": article["author"],
            "fullNews": article["fullNews"],
            "newsURL": article["newsURL"],
            "newsImgURL": article["newsImgURL"],
            "newsDate": article["newsDate"]
        }

        texts.append(text)
        ids.append(document_id)
        metadata_list.append(metadata)

print(f"Collected {len(texts)} unique articles")


# -------- Guard Clause --------

if not texts:
    print("No articles found. Exiting.")
    sys.exit()


# -------- Batch Embedding --------

print("Generating embeddings...")

embeddings = model.encode(
    texts,
    batch_size=32,
    show_progress_bar=True
)

print(f"Generated {len(embeddings)} embeddings")


# -------- Prepare Pinecone Vectors --------

vectors = []

for i in range(len(ids)):
    vectors.append(
        (
            ids[i],
            embeddings[i].tolist(),
            metadata_list[i]
        )
    )


# -------- Batch Upsert --------

batch_size = 100

print("Uploading vectors to Pinecone...")

for i in range(0, len(vectors), batch_size):

    batch = vectors[i:i + batch_size]

    index.upsert(
        vectors=batch,
        namespace=namespace
    )

    print(f"Uploaded batch {i // batch_size + 1}")


print("Update completed successfully.")