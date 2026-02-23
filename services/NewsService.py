import os
import json
import logging
from dotenv import dotenv_values
from flask import jsonify
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_community.llms import HuggingFaceEndpoint

from models.NewsModel import CybernewsDB
from services.CacheService import CacheService

logger = logging.getLogger(__name__)

env_vars = dotenv_values(".env")
HUGGINGFACEHUB_API_TOKEN = env_vars.get("HUGGINGFACE_TOKEN")

# Only set environment variable if token exists
if HUGGINGFACEHUB_API_TOKEN:
    os.environ["HUGGINGFACEHUB_API_TOKEN"] = HUGGINGFACEHUB_API_TOKEN
else:
    logger.warning("⚠ HUGGINGFACE_TOKEN not found in .env file")

class NewsService:
    def __init__(self , model_name) -> None:
        self.db = CybernewsDB()
        self.cache = CacheService()
        self.model_name = model_name
        self.llm = None
        self.available = False

        # Load the LLM configuration
        try:
            with open('config/llm_config.json') as f:
                llm_config = json.load(f)

            repo_id = llm_config.get(model_name)
            
            if not repo_id:
                logger.error(f"Model '{model_name}' not found in llm_config.json")
                return
            
            if not HUGGINGFACEHUB_API_TOKEN:
                logger.error("HUGGINGFACE_TOKEN not configured")
                return
            
            self.llm = HuggingFaceEndpoint(
                    repo_id=repo_id, temperature=0.5, token=HUGGINGFACEHUB_API_TOKEN
                )
            self.available = True
            logger.info(f"✓ LLM service initialized: {model_name}")
        except Exception as e:
            logger.error(f"⚠ Failed to initialize LLM service: {e}")
            self.available = False
        
        self.news_format = "[title, source, date(DD/MM/YYYY), news url];"
        self.news_number = 10

    """
    Return news while checking if keyword has been specified or not
    """

    def getNews(self, user_keywords=None):
        """
        Return news with response caching.
        Caches final LLM output to avoid expensive inference on repeated requests.
        Returns demo/error data if service unavailable.
        """
        # Check if service is available
        if not self.available or self.llm is None:
            logger.warning(f"⚠ LLM service unavailable. Returning demo response.")
            return self.get_demo_response(user_keywords)
        
        # Generate cache key based on model and keywords
        cache_key = f"news:response:{self.model_name}:keywords={user_keywords or 'all'}"
        
        # Try to get from response cache first
        cached_response = self.cache.get(cache_key)
        if cached_response is not None:
            logger.info(f"✓ Response retrieved from cache (model: {self.model_name})")
            return cached_response
        
        # Fetch news data from db (uses data-layer cache)
        news_data = self.db.get_news_collections()
        
        # If no news available, return demo
        if not news_data:
            logger.warning("⚠ No news data available. Returning demo response.")
            return self.get_demo_response(user_keywords)
        
        news_data = news_data[:50]  # limit to 50 due to LLM context limit

        template = """Question: {question}
        Answer: Let's think step by step."""

        prompt = PromptTemplate.from_template(template)

        # Determine which messages template to load
        if user_keywords:
            messages_template_path = 'prompts/withkey.json'
        else:
            messages_template_path = 'prompts/withoutkey.json'
       
        # Load the messages template from the JSON file
        try:
            messages = self.load_json_file(messages_template_path)
        except Exception as e:
            logger.error(f"Could not load prompt template: {e}")
            return self.get_demo_response(user_keywords)

        # Replace placeholders in the messages
        for message in messages:
            if message['role'] == 'user' and '<news_data_placeholder>' in message['content']:
                message['content'] = message['content'].replace('<news_data_placeholder>', str(news_data))
            if user_keywords and message['role'] == 'user' and '<user_keywords_placeholder>' in message['content']:
                message['content'] = message['content'].replace('<user_keywords_placeholder>', str(user_keywords))
            if message['role'] == 'user' and '{news_format}' in message['content']:
                message['content'] = message['content'].replace('{news_format}', self.news_format)
            if message['role'] == 'user' and '{news_number}' in message['content']:
                message['content'] = message['content'].replace('{news_number}', str(self.news_number))

        # Create the LLMChain with the prompt and llm
        try:
            logger.info(f"Invoking LLM (model: {self.model_name})...")
            llm_chain = LLMChain(prompt=prompt, llm=self.llm)
            output = llm_chain.invoke(messages)
        except Exception as e:
            logger.error(f"LLM invocation failed: {e}")
            return self.get_demo_response(user_keywords)

        # Convert news data into JSON format
        news_JSON = self.toJSON(output['text'])
        
        # Cache the response
        self.cache.set(cache_key, news_JSON)
  
        return news_JSON
    
    def get_demo_response(self, user_keywords=None):
        """Return demo response when service is unavailable"""
        demo_data = [
            {
                "title": "[DEMO] Cybersecurity Alert System",
                "source": "B0Bot Demo",
                "date": "22/11/2025",
                "url": "https://b0bot.example.com"
            },
            {
                "title": "[DEMO] Cloud Security Best Practices",
                "source": "B0Bot Demo",
                "date": "21/11/2025",
                "url": "https://b0bot.example.com"
            }
        ]
        if user_keywords:
            demo_data.append({
                "title": f"[DEMO] News related to {user_keywords}",
                "source": "B0Bot Demo",
                "date": "20/11/2025",
                "url": "https://b0bot.example.com"
            })
        return demo_data

 
    """
    deal requests with wrong route
    """

    def notFound(self, error):
        return jsonify({"error": error}), 404
    
    """
    Load JSON file
    """
    
    def load_json_file(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        return data

    """
    Convert news given by Huggingface endpoint API into JSON format.
    """

    def toJSON(self, data: str):
        if len(data) == 0:
            return {}
        news_list = data.split("\n")
        news_list_json = []
        news_list.pop(0)
        for item in news_list:
            # Avoid dirty data
            if len(item) == 0:
                continue
            # Remove leading and trailing square brackets and split by comma and strip extra spaces
            data_list = [item.strip().strip('"') for item in item.strip('[').strip(']').split(',')]
            data_list = [val.strip() for val in data_list]

            for i in data_list:
                print(i)
                print("----")
                
            print(data_list)
            # Assign default values for missing elements
            start_index = data_list[0].find('[') if len(data_list) > 0 else -1
            end_index = data_list[3].find(']') if len(data_list) > 3 else -1
            title = data_list[0][start_index+1:] if len(data_list) > 0 else "No title provided"
            source = data_list[1] if len(data_list) > 1 else "No source provided"
            date = data_list[2] if len(data_list) > 2 else "No date provided"
            url = data_list[3][:end_index-1] if len(data_list) > 3 else "No URL provided"

            news_item = {
                "title": title,
                "source": source,
                "date": date,
                "url": url,
            }
            news_list_json.append(news_item)

        news_list_json.pop()
        return news_list_json
