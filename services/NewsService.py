import os
import re
import json
from dotenv import dotenv_values
from flask import jsonify
from langchain_classic.chains import LLMChain
from langchain_classic.prompts import PromptTemplate
from langchain_community.llms import HuggingFaceEndpoint

from models.NewsModel import CybernewsDB
env_vars = dotenv_values(".env")
HUGGINGFACEHUB_API_TOKEN = env_vars.get("HUGGINGFACE_TOKEN")
# os.environ["HUGGINGFACEHUB_API_TOKEN"] = HUGGINGFACEHUB_API_TOKEN
class NewsService:
    def __init__(self, model_name=None) -> None:
        self.db = CybernewsDB()
        self.llm = None
        self.model_name = model_name

        # Only load the LLM configuration if a model_name is provided
        if model_name:
            with open('config/llm_config.json') as f:
                llm_config = json.load(f)

            repo_id = llm_config.get(model_name)
            
            if not repo_id:
                raise ValueError(f"Model '{model_name}' not found in llm_config.json")
            
            self.llm = HuggingFaceEndpoint(
                repo_id=repo_id, temperature=0.5, token=HUGGINGFACEHUB_API_TOKEN
            )
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

        # Build a numbered article list for the LLM (URLs are NOT sent)
        numbered_list_lines = []
        article_metadata = {}  # index -> full metadata dict
        for i, doc in enumerate(news_data, start=1):
            headline = doc.get('headlines', 'N/A')
            source = doc.get('author', 'N/A')
            date = doc.get('newsDate', 'N/A')
            numbered_list_lines.append(f"[{i}] {headline} — {source} — {date}")
            article_metadata[i] = doc

        numbered_list_str = "\n".join(numbered_list_lines)

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
                message['content'] = message['content'].replace('<news_data_placeholder>', numbered_list_str)
            if user_keywords and message['role'] == 'user' and '<user_keywords_placeholder>' in message['content']:
                message['content'] = message['content'].replace('<user_keywords_placeholder>', str(user_keywords))
            if message['role'] == 'user' and '{news_number}' in message['content']:
                message['content'] = message['content'].replace('{news_number}', str(self.news_number))

        # Create the LLMChain with the prompt and llm
        llm_chain = LLMChain(prompt=prompt, llm=self.llm)
        output = llm_chain.invoke(messages)

        # Resolve selected indices back to full article metadata
        news_JSON = self.resolve_indices(output['text'], article_metadata)
  
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
    Parse the LLM output for selected article indices and resolve them
    to full article metadata. URLs are never taken from LLM output.
    """

    @staticmethod
    def resolve_indices(llm_output: str, article_metadata: dict):
        if not llm_output or len(llm_output.strip()) == 0:
            return []

        # Extract all integers from the LLM output
        raw_indices = re.findall(r'\d+', llm_output)

        seen = set()
        news_list_json = []
        for idx_str in raw_indices:
            idx = int(idx_str)
            if idx in seen or idx not in article_metadata:
                continue
            seen.add(idx)
            doc = article_metadata[idx]
            news_item = {
                "title": doc.get('headlines', 'No title provided'),
                "source": doc.get('author', 'No source provided'),
                "date": doc.get('newsDate', 'No date provided'),
                "url": doc.get('newsURL', 'No URL provided'),
            }
            news_list_json.append(news_item)

        return news_list_json
