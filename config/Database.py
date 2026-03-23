from dotenv import dotenv_values
from pinecone import Pinecone
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

PINECONE_API = dotenv_values(".env").get("PINECONE_API_KEY")

if not PINECONE_API:
    raise ValueError("PINECONE_API_KEY is missing. Please set it in your .env file. See .env.example for reference.")

client = Pinecone(api_key=PINECONE_API)
index_name = "cybernews-index"