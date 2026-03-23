import os
import json
from dotenv import dotenv_values
from flask import jsonify
from langchain_classic.chains import LLMChain
from langchain_classic.prompts import PromptTemplate
from langchain_community.llms import HuggingFaceEndpoint

from models.NewsModel import CybernewsDB
env_vars = dotenv_values(".env")
HUGGINGFACEHUB_API_TOKEN = env_vars.get("HUGGINGFACE_TOKEN")

if not HUGGINGFACEHUB_API_TOKEN:
    raise ValueError("HUGGINGFACE_TOKEN is missing. Please set it in your .env file. See .env.example for reference.")

_LLM_CONFIG_CACHE = None
_LLM_CLIENT_CACHE = {}

def _get_llm_config():
    global _LLM_CONFIG_CACHE
    if _LLM_CONFIG_CACHE is None:
        with open('config/llm_config.json') as f:
            _LLM_CONFIG_CACHE = json.load(f)
    return _LLM_CONFIG_CACHE

def _get_llm_client(model_name):
    if model_name not in _LLM_CLIENT_CACHE:
        llm_config = _get_llm_config()
        repo_id = llm_config.get(model_name)
        if not repo_id:
            raise ValueError(f"Model '{model_name}' not found in llm_config.json")
        _LLM_CLIENT_CACHE[model_name] = HuggingFaceEndpoint(
            repo_id=repo_id, temperature=0.5, token=HUGGINGFACEHUB_API_TOKEN
        )
    return _LLM_CLIENT_CACHE[model_name]

class NewsService:
    def __init__(self, model_name=None) -> None:
        self.db = CybernewsDB()
        self.llm = None
        self.model_name = model_name

        if model_name:
            self.llm = _get_llm_client(model_name)
        self.news_format = "[title, source, date(DD/MM/YYYY), news url];"
        self.news_number = 10

    """
    Return news while checking if keyword has been specified or not
    """

    def getNews(self, user_keywords=None, llm=False):
    # Fetch news data from db:
    # Only fetch data with valid `author` and `newsDate`
    # Drop field "id" from collection

        if user_keywords:
            news_data = self.db.get_news_collections(is_keyword=True, keyword=user_keywords)
        else:
            news_data = self.db.get_news_collections()
        
        if not llm:
            # Map raw database results to the standard format if LLM is skipped
            return [
                {
                    "title": doc.get('headlines', 'No title provided'),
                    "source": doc.get('author', 'No source provided'),
                    "date": doc.get('newsDate', 'No date provided'),
                    "url": doc.get('newsURL', 'No URL provided'),
                }
                for doc in news_data[:self.news_number]
            ]
            
        news_data = news_data[:50] # limit the number of news to 50 , as LLMs have a context limit

        template = """Question: {question}
        Answer: Let's think step by step."""

        prompt = PromptTemplate.from_template(template)

        # Determine which messages template to load
        if user_keywords:
            messages_template_path = 'prompts/withkey.json'
        else:
            messages_template_path = 'prompts/withoutkey.json'
       
        # Load the messages template from the JSON file
        messages = self.load_json_file(messages_template_path)

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
        llm_chain = LLMChain(prompt=prompt, llm=self.llm)
        output = llm_chain.invoke(messages)

        # Convert news data into JSON format
        news_JSON = self.toJSON(output['text'])
  
        return news_JSON

 
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
        if not data or len(data) == 0:
            return []
        news_list = data.split("\n")
        news_list_json = []
        
        if len(news_list) <= 1:
            return []
            
        news_list.pop(0)
        for item in news_list:
            if len(item) == 0:
                continue
            try:
                data_list = [item.strip().strip('"') for item in item.strip('[').strip(']').split(',')]
                data_list = [val.strip() for val in data_list]
                
                if len(data_list) < 4:
                    continue
                    
                start_index = data_list[0].find('[') if len(data_list) > 0 else -1
                end_index = data_list[3].find(']') if len(data_list) > 3 else -1
                title = data_list[0][start_index+1:] if len(data_list) > 0 and start_index >= 0 else data_list[0]
                source = data_list[1] if len(data_list) > 1 else "No source provided"
                date = data_list[2] if len(data_list) > 2 else "No date provided"
                url = data_list[3][:end_index-1] if len(data_list) > 3 and end_index > 0 else data_list[3]

                news_item = {
                    "title": title,
                    "source": source,
                    "date": date,
                    "url": url,
                }
                news_list_json.append(news_item)
            except (IndexError, AttributeError):
                continue
                
        if news_list_json:
            news_list_json.pop()
        return news_list_json
