from dotenv import dotenv_values
from pinecone import Pinecone
import os
import sys
import logging

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

logger = logging.getLogger(__name__)

PINECONE_API = dotenv_values(".env").get("PINECONE_API_KEY")
index_name = "cybernews-index"

# Initialize Pinecone with graceful fallback
client = None
if PINECONE_API:
    try:
        client = Pinecone(api_key=PINECONE_API)
        logger.info("✓ Pinecone initialized successfully")
    except Exception as e:
        logger.warning(f"⚠ Pinecone initialization failed: {e}")
        logger.warning("⚠ App will run without database access. Check API key.")
        client = None
else:
    logger.warning("⚠ PINECONE_API_KEY not found in .env file")
    logger.warning("⚠ App will run without database access.")