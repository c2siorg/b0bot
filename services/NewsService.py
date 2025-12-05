import os
from flask import g
import json
import requests
from dotenv import dotenv_values
from models.NewsModel import CybernewsDB

# --- MODERN IMPORTS (2025) ---
from langchain_huggingface import HuggingFaceEndpoint
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
# -----------------------------
env_vars = dotenv_values(".env")
HUGGINGFACEHUB_API_TOKEN = env_vars.get("HUGGINGFACE_TOKEN")
os.environ["HUGGINGFACEHUB_API_TOKEN"] = HUGGINGFACEHUB_API_TOKEN
class NewsService:
    def __init__(self , model_name) -> None:
        self.db = CybernewsDB()

        # Load the LLM configuration
        with open('config/llm_config.json') as f:
            llm_config = json.load(f)

        repo_id = llm_config.get(model_name) # loading the llm 
        
        if not repo_id:
            raise ValueError(f"Model '{model_name}' not found in llm_config.json")
        
        self.llm = HuggingFaceEndpoint(
                repo_id=repo_id, temperature=0.5, token=HUGGINGFACEHUB_API_TOKEN
            )
        self.news_format = "[title, source, date(DD/MM/YYYY), news url];"
        self.news_number = 10

    """
    Return news while checking if keyword has been specified or not
    """

    def getNews(self, user_keywords=None):
        # 1. Fetch Data from Pinecone
        news_data = self.db.get_news_collections()

        if not news_data:
            return "No news found in the database."

        # 2. Format the news for the AI
        # 2. Format the news for the AI (Updated for Dictionary Access)
        formatted_news = "\n".join([
            f"- {item.get('metadata', {}).get('title', 'No Title')}: {item.get('metadata', {}).get('summary', 'No summary')}"
            for item in news_data
        ])
        
        # 3. Create the Modern Chain (Prompt | Model | Parser)
        prompt_template = PromptTemplate(
            input_variables=["news_content"],
            template="You are a tech news reporter. Summarize these stories into a concise briefing:\n\n{news_content}"
        )
        
        # The "|" symbol is the new way to connect components
        chain = prompt_template | self.llm | StrOutputParser()
        
        # 4. Run it
        try:
            return chain.invoke({"news_content": formatted_news})
        except Exception as e:
            return f"Error generating summary: {str(e)}"

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
