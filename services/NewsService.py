import os
import json
from dotenv import dotenv_values
from flask import jsonify
from typing import List

from pydantic import BaseModel, HttpUrl
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser

from models.NewsModel import CybernewsDB


# Load environment variables
env_vars = dotenv_values(".env")
HUGGINGFACEHUB_API_TOKEN = env_vars.get("HUGGINGFACE_TOKEN")


# -----------------------------
# Structured Schema Definitions
# -----------------------------

class NewsItem(BaseModel):
    title: str
    source: str
    date: str
    url: HttpUrl


class NewsResponse(BaseModel):
    items: List[NewsItem]


# -----------------------------
# News Service
# -----------------------------

class NewsService:
    def __init__(self, model_name) -> None:
        self.db = CybernewsDB()

        # Load LLM configuration
        with open("config/llm_config.json") as f:
            llm_config = json.load(f)

        repo_id = llm_config.get(model_name)

        if not repo_id:
            raise ValueError(f"Model '{model_name}' not found in llm_config.json")

        self.repo_id = repo_id

        # HF Router-backed Chat Model
        self.llm = ChatOpenAI(
            model=self.repo_id,
            temperature=0,  # MUST be 0 for structured output stability
            api_key=HUGGINGFACEHUB_API_TOKEN,
            base_url="https://router.huggingface.co/v1",
        )

        # Structured output parser
        self.parser = PydanticOutputParser(pydantic_object=NewsResponse)

    # -----------------------------
    # Get News
    # -----------------------------

    def getNews(self, user_keywords=None):
        news_data = self.db.get_news_collections()

        print("DB COUNT:", len(news_data))

        # Limit input size
        news_data = news_data[:10]

        # Reduce to essential fields only
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

        prompt = PromptTemplate(
            template="""
You are a cybersecurity news formatter.

Extract strictly from the provided JSON.
Return ONLY valid JSON.
Do NOT invent values.
Do NOT return null.
Do NOT add explanation.

{format_instructions}

User Keywords:
{user_keywords}

News Data:
{news_data}
""",
            input_variables=["news_data", "user_keywords"],
            partial_variables={
                "format_instructions": self.parser.get_format_instructions()
            },
        )

        chain = prompt | self.llm | self.parser

        try:
            result = chain.invoke({
                "news_data": serialized_news,
                "user_keywords": user_keywords if user_keywords else "None"
            })

            return result.dict()["items"]

        except Exception as e:
            print("STRUCTURED OUTPUT FAILED:", e)
            return []

    # -----------------------------
    # 404 Handler
    # -----------------------------

    def notFound(self, error):
        return jsonify({"error": error}), 404