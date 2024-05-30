import os
from dotenv import dotenv_values
from flask import jsonify
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_community.llms import HuggingFaceEndpoint

from models.NewsModel import CybernewsDB
env_vars = dotenv_values(".env")
HUGGINGFACEHUB_API_TOKEN = env_vars.get("HUGGINGFACE_TOKEN")
os.environ["HUGGINGFACEHUB_API_TOKEN"] = HUGGINGFACEHUB_API_TOKEN
class NewsService:
    def __init__(self) -> None:
        self.db = CybernewsDB()
        repo_id = "mistralai/Mistral-7B-Instruct-v0.2" # loading the llm

        self.llm = HuggingFaceEndpoint(
                repo_id=repo_id, temperature=0.5, token=HUGGINGFACEHUB_API_TOKEN
            )
        self.news_format = "title [source, date(MM/DD/YYYY), news url];"
        self.news_number = 10

    """
    Return news without considering keywords
    """

    def getNews(self):
        # fetch news data from db:
        # only fetch data with valid `author` and `newsDate`
        # drop field "id" from collection
        news_data = self.db.get_news_collections().find(
            {"author": {"$ne": "N/A"}, "newsDate": {"$ne": "N/A"}},
            {
                "headlines": 1,
                "newsDate": 1,
                "author": 1,
                "newsURL": 1,
                "_id": 0,
            },
        )
        news_data = list(news_data)

        template = """Question: {question}
        Answer: Let's think step by step."""

        prompt = PromptTemplate.from_template(template)

        messages = [
            {
                "role": "system",
                "content": "You are a news analyzer that will read the given cyber security news and return the answer based on the user's requirement.",
            },
            {"role": "user", "content": str(news_data)},
            {"role": "assistant","content":"I have read the news you provided. Now please tell me your request."},
            {"role": "user","content":"""Please give me a list of the most recent cybersecurity news based on the news given above.
                            Indicate the source and date.
                            Each news should be strictly in the format of {news_format}.
                            Your reply should be news-only, without adding any of your conversational content.
                            Do not use bullet points.
                            Do not use regex.
                            Only give the output in the required format.
                            Do not stop generating the answer until it is complete.
                            Return at most {news_number} news.""".format(
                                news_format=self.news_format, news_number=self.news_number
                            )}
        ]

        llm_chain = LLMChain(prompt=prompt, llm=self.llm)
        output=llm_chain.invoke(messages)
        print(output['text'])

        # convert news data into JSON format
        news_JSON = self.toJSON(output['text'])

        return news_JSON

    """
    return news based on certain keywords
    """

    def getNewsWithKeywords(self, user_keywords):
        # fetch news data from db:
        # only fetch data with valid `author` and `newsDate`
        # drop field "id" from collection
        news_data = self.db.get_news_collections().find(
            {"author": {"$ne": "N/A"}, "newsDate": {"$ne": "N/A"}},
            {
                "headlines": 1,
                "newsDate": 1,
                "author": 1,
                "newsURL": 1,
                "_id": 0,
            },
        )
        news_data = list(news_data)

        template = """Question: {question}
        Answer: Let's think step by step."""

        prompt = PromptTemplate.from_template(template)

        messages = [
            {
                "role": "system",
                "content": "You are a news analyzer that will read the given cyber security news and return the answer based on the user's requirement.",
            },
            {"role": "user", "content": str(news_data)},
            {"role": "assistant","content":"I have read the news you provided. Now please give me your keywords."},
            {"role": "user", "content": str(user_keywords)},
            {"role": "assistant","content":"I have read the keywords you provided. Now please tell me how you want me to generate the answers."},
            {"role": "user","content":"""Please give me a list of the most recent cybersecurity news based on the news and keyword given above.
                            Indicate the source and date.
                            Each news should be strictly in the format of {news_format}.
                            Your reply should be news-only, without adding any of your conversational content.
                            Do not use bullet points.
                            Do not use regex.
                            Only give the output in the required format.
                            Do not stop generating the answer until it is complete.
                            Return at most {news_number} news.""".format(
                                news_format=self.news_format, news_number=self.news_number
                            )}
        ]

        llm_chain = LLMChain(prompt=prompt, llm=self.llm)
        output=llm_chain.invoke(messages)
        print(output['text'])

        # convert news data into JSON format
        news_JSON = self.toJSON(output['text'])

        return news_JSON

    """
    deal requests with wrong route
    """

    def notFound(self, error):
        return jsonify({"error": error}), 404

    """
    Convert news given by OpenAI API into JSON format.
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
            # Split the string at the first occurrence of '('
            if "[" in item:
                title, remaining = item.split("[", 1)
            else:
                title = item
                remaining = ""
            title = title.strip(' "')
            # Extract the source by splitting at ',' and removing leading/trailing whitespace
            if "," not in remaining:
                source = "N/A"
                date = "N/A"
                url = "N/A"
            else:
                source, date, url = remaining.split(",")

            source = source.strip(' "')
            date = date.strip(' "')
            url = url.strip(" ];")

            # Create a dictionary for each news item and append it to the news_list
            news_item = {
                "title": title,
                "source": source,
                "date": date,
                "url": url,
            }
            news_list_json.append(news_item)

        return jsonify(news_list_json)
