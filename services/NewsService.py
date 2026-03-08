import os
import json
from dotenv import load_dotenv
from flask import jsonify
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_huggingface import HuggingFaceEndpoint
from models.NewsModel import CybernewsDB
from utils.redis_client import RedisClient
load_dotenv()


class NewsService:
    def __init__(self , model_name) -> None:
        self.db = CybernewsDB()
        self.redis = RedisClient(expiry=3600)
        # Load the LLM configuration
        with open('config/llm_config.json') as f:
            llm_config = json.load(f)

        self.model_name = llm_config.get(model_name) # loading the llm
        
        if not model_name:
            raise ValueError(f"Model '{self.model_name}' not found in llm_config.json")
        
        self.llm = HuggingFaceEndpoint(
             temperature=0.5, model=self.model_name
        )
        self.news_format = "[title, source, date(DD/MM/YYYY), news url];"
        self.news_number = 10

    """
    Return news while checking if keyword has been specified or not
    """

    def getNews(self, user_keywords=None):
        # Fetch news data from db:
        # Only fetch data with valid `author` and `newsDate`
        # Drop field "id" from collection
        cache_key = f"news:{self.model_name}"
        if user_keywords:
            cache_key += f":{user_keywords}"

        # Check if the data is cached
        cached_news = self.redis.get(cache_key)
        if cached_news:
            return cached_news

        news_data = self.db.get_news_collections()
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
        # Cache the data
        self.redis.set(cache_key, news_JSON)

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
        cache_key = f"file:{file_path}"
        cached_file = self.redis.get(cache_key)
        if cached_file:
            return cached_file

        # If not cached, load from disk
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)

        # Cache file content with longer expiry (1 day)
        self.redis.set(cache_key, data)
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
