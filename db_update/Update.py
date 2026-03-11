import sys
import os
from dotenv import dotenv_values
from pinecone import Pinecone, ServerlessSpec
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from cybernews.CyberNews import CyberNews

PINECONE_API = dotenv_values(".env").get("PINECONE_API_KEY")

# Configure client
pc = Pinecone(api_key=PINECONE_API)
index_name = "cybernews-hybrid-test-2"



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
def update_database(overwrite=(len(sys.argv) > 1 and sys.argv[1] == '--overwrite')):
    # Delete the index if overwrite is requested
    if overwrite and index_name in pc.list_indexes().names():
        pc.delete_index(index_name)
        print(f"Deleted existing index: {index_name}")

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
    from sentence_transformers import SentenceTransformer, SparseEncoder
    import numpy as np
    
    # Initialize native local embedding models
    print("Loading local dense model (all-MiniLM-L6-v2)...")
    dense_model = SentenceTransformer("all-MiniLM-L6-v2")
    
    print("Loading local sparse model (prithivida/Splade_PP_en_v2)...")
    sparse_model = SparseEncoder("prithivida/Splade_PP_en_v2")
    
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
                # 1. Generate Dense Vector locally
                dense_vector = dense_model.encode(text).tolist()
                
                # 2. Generate Sparse Vector locally
                emb = sparse_model.encode(text)
                if hasattr(emb, 'to_dense'):
                    emb = emb.to_dense()
                if hasattr(emb, 'cpu'):
                    emb = emb.cpu()
                    
                emb_array = np.array(emb)
                
                # Flatten in case of batch dimension (1, vocab_size)
                if len(emb_array.shape) == 2:
                    emb_array = emb_array[0]
                    
                indices = np.nonzero(emb_array)[0].tolist()
                values = [float(emb_array[i]) for i in indices]
                sparse_vector = {"indices": indices, "values": values}

                # Construct record exactly as per Pinecone documentation
                record = {
                    "id": str(article.get("id", "")),
                    "values": dense_vector,
                    "sparse_values": sparse_vector,
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

if __name__ == "__main__":
    update_database()
