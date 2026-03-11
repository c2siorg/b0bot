import sys
import os
import requests
from dotenv import dotenv_values
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer

# Setup path for local modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from cybernews.CyberNews import CyberNews
except ImportError as e:
    print(f" Error: Could not find 'cybernews' module. Ensure you are running from the project root. {e}")
    sys.exit(1)

# Load environment variables
config = dotenv_values(".env")
PINECONE_API = config.get("PINECONE_API_KEY")

# --- 1. ROBUST DATABASE INITIALIZATION ---
try:
    if not PINECONE_API:
        raise ValueError("PINECONE_API_KEY is missing from your .env file!")
    
    pc = Pinecone(api_key=PINECONE_API)
    print("✅ Connected to Pinecone successfully.")
    
    index_name = "cybernews-index"

    # Handle index lifecycle safely
    existing_indexes = pc.list_indexes().names()
    if index_name in existing_indexes:
        pc.delete_index(index_name)
        print(f"🗑️ Deleted existing index: {index_name}")

    if index_name not in existing_indexes:
        print(f"🏗️ Creating new index: {index_name}...")
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

except Exception as e:
    print(f"❌ Database Initialization Error: {e}")
    sys.exit(1)

namespace = "c2si"

# --- 2. MODEL AND SCRAPER INITIALIZATION ---
try:
    model = SentenceTransformer('all-MiniLM-L6-v2')
    news = CyberNews()
    print("🤖 AI Model and Scraper initialized.")
except Exception as e:
    print(f"❌ Initialization Error (Model/Scraper): {e}")
    sys.exit(1)

# --- 3. ROBUST NEWS FETCHING ---
newsBox = dict()
categories = ["general", "cyberAttack", "vulnerability", "malware", "security", "dataBreach"]

print("📡 Fetching news updates...")
for category in categories:
    try:
        # Fetching news from the local scraper module
        fetched_news = news.get_news(category)
        newsBox[f"{category}_news"] = fetched_news
        print(f"   ✔️  {category}: Found {len(fetched_news)} articles.")
    except Exception as e:
        print(f"   ⚠️  Warning: Could not fetch {category} news: {e}")
        newsBox[f"{category}_news"] = []


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

# --- 4. DATA PROCESSING AND UPSERT ---
print(f"📤 Processing and uploading vectors to namespace: {namespace}...")

for news_type, articles in newsBox.items():
    for article in articles:
        try:
            # Combine headline and full news for embedding
            text = f"{article.get('headlines', '')} {article.get('fullNews', '')}"
            
            # Convert text to vector
            vector = model.encode(text).tolist()
            
            # Prepare the document ID
            document_id = str(article.get("id", "unknown"))
            
            # Prepare metadata with safety checks
            metadata = {
                "headlines": article.get("headlines", "N/A"),
                "author": article.get("author", "Unknown"),
                "fullNews": article.get("fullNews", ""),
                "newsURL": article.get("newsURL", ""),
                "newsImgURL": article.get("newsImgURL", ""),
                "newsDate": article.get("newsDate", "")
            }
            
            # Upsert the vector with metadata into Pinecone
            index.upsert([(document_id, vector, metadata)], namespace=namespace)
            
        except Exception as e:
            print(f"   ❌ Error processing article {article.get('id')}: {e}")
            continue # Skip failed article and move to next

print("✨ Database update complete!")