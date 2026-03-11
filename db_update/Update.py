import sys
import os
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer

# Load environment variables from .env
load_dotenv()
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from cybernews.CyberNews import CyberNews

PINECONE_API = os.environ.get("PINECONE_API_KEY")

# Configure client
pc = Pinecone(api_key=PINECONE_API)
index_name = "cybernews-hybrid-test"

# Delete the index if it already exists for testing
# if index_name in pc.list_indexes().names():
#     pc.delete_index(index_name)
#     print(f"Deleted existing index: {index_name}")

# Create the hybrid index (metric='dotproduct' is recommended for hybrid)
if index_name not in pc.list_indexes().names():
    pc.create_index(
        name=index_name, 
        dimension=384, 
        metric='dotproduct', 
        spec=ServerlessSpec(
            cloud='aws',
            region='us-east-1'
        )
    )

# Connect to the index
index = pc.Index(index_name)
namespace = "c2si"

# Different types of news
news = CyberNews()
newsBox = dict()
newsBox["general_news"] = news.get_news("general")
newsBox["cyber_attack_news"] = news.get_news("cyberAttack")
newsBox["vulnerability_news"] = news.get_news("vulnerability")
newsBox["malware_news"] = news.get_news("malware")
newsBox["security_news"] = news.get_news("security")
newsBox["data_breach_news"] = news.get_news("dataBreach")   

# Convert news articles to vectors and upsert into Pinecone
all_records = []
for news_type, articles in newsBox.items():
    if not articles:
        continue
    for article in articles:
        headlines = article.get("headlines")
        full_news = article.get("fullNews")
        if not headlines or not full_news:
            continue
            
        text = str(headlines) + " " + str(full_news)
        
        try:
            # 1. Generate Dense Vector using Pinecone Inference
            dense_response = pc.inference.embed(
                model="llama-text-embed-v2",
                inputs=[text],
                parameters={"dimension": 384, "input_type": "passage"}
            )import sys
import os
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer

# Load environment variables from .env
load_dotenv()
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from cybernews.CyberNews import CyberNews

PINECONE_API = os.environ.get("PINECONE_API_KEY")

# Configure client
pc = Pinecone(api_key=PINECONE_API)
index_name = "cybernews-hybrid-test"

# Delete the index if it already exists for testing
# if index_name in pc.list_indexes().names():
#     pc.delete_index(index_name)
#     print(f"Deleted existing index: {index_name}")

# Create the hybrid index (metric='dotproduct' is recommended for hybrid)
if index_name not in pc.list_indexes().names():
    pc.create_index(
        name=index_name, 
        dimension=384, 
        metric='dotproduct', 
        spec=ServerlessSpec(
            cloud='aws',
            region='us-east-1'
        )
    )

# Connect to the index
index = pc.Index(index_name)
namespace = "c2si"

# Different types of news
news = CyberNews()
newsBox = dict()
newsBox["general_news"] = news.get_news("general")
newsBox["cyber_attack_news"] = news.get_news("cyberAttack")
newsBox["vulnerability_news"] = news.get_news("vulnerability")
newsBox["malware_news"] = news.get_news("malware")
newsBox["security_news"] = news.get_news("security")
newsBox["data_breach_news"] = news.get_news("dataBreach")   

# Convert news articles to vectors and upsert into Pinecone
all_records = []
for news_type, articles in newsBox.items():
    if not articles:
        continue
    for article in articles:
        headlines = article.get("headlines")
        full_news = article.get("fullNews")
        if not headlines or not full_news:
            continue
            
        text = str(headlines) + " " + str(full_news)
        
        try:
            # 1. Generate Dense Vector using Pinecone Inference
            dense_response = pc.inference.embed(
                model="llama-text-embed-v2",
                inputs=[text],
                parameters={"dimension": 384, "input_type": "passage"}
            )
            
            # 2. Generate Sparse Vector using Pinecone Inference
            sparse_response = pc.inference.embed(
                model="pinecone-sparse-english-v0",
                inputs=[text],
                parameters={"input_type": "passage"}
            )

            # Construct record exactly as per Pinecone documentation
            record = {
                "id": str(article.get("id", "")),
                "values": dense_response[0].values,
                "sparse_values": {
                    "indices": sparse_response[0].sparse_indices,
                    "values": sparse_response[0].sparse_values
                },
                "metadata": {
                    "headlines": str(headlines),
                    "author": str(article.get("author", "Unknown")),
                    "fullNews": str(full_news),
                    "newsURL": str(article.get("newsURL", "")),
                    "newsImgURL": str(article.get("newsImgURL", "")),
                    "newsDate": str(article.get("newsDate", ""))
                }
            }
            all_records.append(record)
            print(f"Prepared article for hybrid indexing: {record['id']}")
            
        except Exception as e:
            print(f"Error processing article {article.get('id')}: {e}")

# Upsert all records in batch
if all_records:
    index.upsert(vectors=all_records, namespace=namespace)
    print(f"Successfully upserted {len(all_records)} hybrid records into {index_name}")

            
            # 2. Generate Sparse Vector using Pinecone Inference
            sparse_response = pc.inference.embed(
                model="pinecone-sparse-english-v0",
                inputs=[text],
                parameters={"input_type": "passage"}
            )

            # Construct record exactly as per Pinecone documentation
            record = {
                "id": str(article.get("id", "")),
                "values": dense_response[0].values,
                "sparse_values": {
                    "indices": sparse_response[0].sparse_indices,
                    "values": sparse_response[0].sparse_values
                },
                "metadata": {
                    "headlines": str(headlines),
                    "author": str(article.get("author", "Unknown")),
                    "fullNews": str(full_news),
                    "newsURL": str(article.get("newsURL", "")),
                    "newsImgURL": str(article.get("newsImgURL", "")),
                    "newsDate": str(article.get("newsDate", ""))
                }
            }
            all_records.append(record)
            print(f"Prepared article for hybrid indexing: {record['id']}")
            
        except Exception as e:
            print(f"Error processing article {article.get('id')}: {e}")

# Upsert all records in batch
if all_records:
    index.upsert(vectors=all_records, namespace=namespace)
    print(f"Successfully upserted {len(all_records)} hybrid records into {index_name}")
