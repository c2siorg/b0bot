import os
import sys
from pinecone import Pinecone
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
client = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index_name = "cybernews-index"