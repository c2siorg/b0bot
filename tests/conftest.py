import os

# Set dummy environment variables to prevent app.py from raising SystemExit 
# during pytest collection when checking validate_env()
os.environ["PINECONE_API_KEY"] = "dummy_pinecone_key"
os.environ["PINECONE_INDEX_NAME"] = "dummy_pinecone_index"
os.environ["HUGGINGFACE_TOKEN"] = "dummy_hf_token"
