import os
import json
from dotenv import dotenv_values
from flask import jsonify

from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

from models.NewsModel import CybernewsDB

env_vars = dotenv_values(".env")
HUGGINGFACEHUB_API_TOKEN = env_vars.get("HUGGINGFACE_TOKEN")


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

        # LangChain Chat Model via HF Router
        self.llm = ChatOpenAI(
            model=self.repo_id,
            temperature=0.5,
            api_key=HUGGINGFACEHUB_API_TOKEN,
            base_url="https://router.huggingface.co/v1",
        )

        self.news_format = "[title | source | date(DD/MM/YYYY) | news url];"
        self.news_number = 10

    def getNews(self, user_keywords=None):
        news_data = self.db.get_news_collections()
        news_data = news_data[:10]

        # Determine prompt template
        if user_keywords:
            messages_template_path = "prompts/withkey.json"
        else:
            messages_template_path = "prompts/withoutkey.json"

        messages = self.load_json_file(messages_template_path)

        # Replace placeholders
        for message in messages:
            if message["role"] == "user" and "<news_data_placeholder>" in message["content"]:
                message["content"] = message["content"].replace(
                    "<news_data_placeholder>", str(news_data)
                )

            if user_keywords and message["role"] == "user" and "<user_keywords_placeholder>" in message["content"]:
                message["content"] = message["content"].replace(
                    "<user_keywords_placeholder>", str(user_keywords)
                )

            if message["role"] == "user" and "{news_format}" in message["content"]:
                message["content"] = message["content"].replace(
                    "{news_format}", self.news_format
                )

            if message["role"] == "user" and "{news_number}" in message["content"]:
                message["content"] = message["content"].replace(
                    "{news_number}", str(self.news_number)
                )

        # LangChain expects a string prompt for LLMChain
        prompt_text = "\n".join([m["content"] for m in messages if m["role"] != "system"])

        prompt = PromptTemplate.from_template("{input}")

        llm_chain = LLMChain(
            llm=self.llm,
            prompt=prompt
        )

        response = llm_chain.invoke({"input": prompt_text})

        output_text = response["text"]

        news_JSON = self.toJSON(output_text)

        return news_JSON

    def notFound(self, error):
        return jsonify({"error": error}), 404

    def load_json_file(self, file_path):
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)
        return data

    def toJSON(self, data: str):
        if not data:
            return []

        news_list = data.split("\n")
        news_list_json = []

        for item in news_list:
            item = item.strip()

            if not item:
                continue

            if not item.startswith("[") or "|" not in item:
                continue

            item = item.strip("[]").strip(";")

            parts = [p.strip() for p in item.split("|")]

            if len(parts) != 4:
                continue

            title, source, date, url = parts

            news_item = {
                "title": title,
                "source": source,
                "date": date,
                "url": url,
            }

            news_list_json.append(news_item)

        return news_list_json