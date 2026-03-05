import os
import json
from dotenv import dotenv_values
from flask import jsonify
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_community.llms import HuggingFaceEndpoint

from models.NewsModel import CybernewsDB

# Load env for local testing
env_vars = dotenv_values(".env")
HUGGINGFACEHUB_API_TOKEN = env_vars.get("HUGGINGFACE_TOKEN")
os.environ["HUGGINGFACEHUB_API_TOKEN"] = HUGGINGFACEHUB_API_TOKEN

class NewsService:
    def __init__(self, model_name) -> None:
        self.db = CybernewsDB()

        # Load the LLM configuration
        try:
            with open('config/llm_config.json') as f:
                llm_config = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError("Critical Error: config/llm_config.json not found.")

        repo_id = llm_config.get(model_name)
        
        if not repo_id:
            raise ValueError(f"Model '{model_name}' not found in llm_config.json")
        
        # Initialize modern LLM endpoint
        self.llm = HuggingFaceEndpoint(
            repo_id=repo_id, 
            temperature=0.1, # Lower temperature for better JSON consistency
            token=HUGGINGFACEHUB_API_TOKEN
        )
        
        self.news_format = '{"title": "string", "source": "string", "date": "DD/MM/YYYY", "url": "string"}'
        self.news_number = 10

    def getNews(self, user_keywords=None):
        """
        Fetches news from DB and uses LCEL to summarize/format via LLM.
        """
        # Fetch data from db
        news_data = self.db.get_news_collections()
        news_data = news_data[:50] 

        # 1. Define the System/User Prompt
        # We use a structured prompt to ensure the LLM understands the JSON requirement
        prompt = ChatPromptTemplate.from_template(
            "You are a Cyber Security Analyst. Summarize the following news data into a valid JSON list.\n"
            "Data: {news_data}\n\n"
            "Keywords to focus on: {keywords}\n"
            "Requirement: Return exactly {number} items in this JSON format: {format}\n"
            "Return ONLY the JSON list. No preamble or explanations."
        )

        # 2. Setup LCEL Chain: Prompt -> LLM -> JSON Parser
        # This replaces the deprecated LLMChain
        parser = JsonOutputParser()
        chain = prompt | self.llm | parser

        # 3. Invoke the chain
        try:
            output = chain.invoke({
                "news_data": str(news_data),
                "keywords": user_keywords if user_keywords else "general cyber security",
                "number": self.news_number,
                "format": self.news_format
            })
            return output
        except Exception as e:
            print(f"Error in LLM Processing: {e}")
            # Fallback to empty list or error message
            return []

    def notFound(self, error):
        """Deal with requests with wrong route."""
        return jsonify({"error": error}), 404
    
    def load_json_file(self, file_path):
        """Standard JSON loader with UTF-8 support."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
