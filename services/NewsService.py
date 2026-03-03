import os
import json
from dotenv import dotenv_values
from flask import jsonify
from typing import List

from pydantic import BaseModel, HttpUrl
from langchain_openai import ChatOpenAI

from models.NewsModel import CybernewsDB


# Load environment variables
env_vars = dotenv_values(".env")
HUGGINGFACEHUB_API_TOKEN = env_vars.get("HUGGINGFACE_TOKEN")


class NewsItem(BaseModel):
    title: str
    source: str
    date: str
    url: HttpUrl


class NewsResponse(BaseModel):
    items: List[NewsItem]


class NewsService:
    def __init__(self, model_name) -> None:
        self.db = CybernewsDB()

        with open("config/llm_config.json") as f:
            llm_config = json.load(f)

        repo_id = llm_config.get(model_name)

        if not repo_id:
            raise ValueError(f"Model '{model_name}' not found in llm_config.json")

        self.repo_id = repo_id

        self.llm = ChatOpenAI(
            model=self.repo_id,
            temperature=0,
            api_key=HUGGINGFACEHUB_API_TOKEN,
            base_url="https://router.huggingface.co/v1",
        )

    def getNews(self, user_keywords=None):
        news_data = self.db.get_news_collections()

        print("DB COUNT:", len(news_data))

        news_data = news_data[:10]

        trimmed_news = [
            {
                "title": item.get("headlines"),
                "source": item.get("author"),
                "date": item.get("newsDate"),
                "url": item.get("newsURL"),
            }
            for item in news_data
        ]

        serialized_news = json.dumps(trimmed_news, indent=2)

        prompt = f"""
You are a cybersecurity news formatter.

Extract ALL items from the provided JSON.
Return exactly one valid JSON object in this format:

{{
  "items": [
    {{
      "title": "...",
      "source": "...",
      "date": "...",
      "url": "..."
    }}
  ]
}}

Do not include explanations.
Do not include markdown.
Return only JSON.

User Keywords:
{user_keywords if user_keywords else "None"}

News Data:
{serialized_news}
"""

        try:
            raw_response = self.llm.invoke(prompt)
            content = raw_response.content.strip()

            # Remove markdown fences if present
            content = content.replace("```json", "").replace("```", "").strip()

            # Extract first valid JSON object only
            decoder = json.JSONDecoder()
            obj, _ = decoder.raw_decode(content)

            # Case 1: wrapped in list
            if isinstance(obj, list):
                obj = obj[0]

            # Case 2: model returned single object
            if "items" not in obj:
                obj = {"items": [obj]}

            validated = NewsResponse(**obj)

            return validated.items

        except Exception as e:
            print("STRUCTURED OUTPUT FAILED:", e)
            return []

    def notFound(self, error):
        return jsonify({"error": error}), 404