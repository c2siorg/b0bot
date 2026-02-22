from dotenv import dotenv_values
from pinecone import Pinecone
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load environment variables
env_vars = dotenv_values(".env")
PINECONE_API = env_vars.get("PINECONE_API_KEY")

# Fetch index name from .env, fallback to "cybernews-index" if not found
index_name = env_vars.get("PINECONE_INDEX_NAME", "cybernews-index")

client = Pinecone(api_key=PINECONE_API)