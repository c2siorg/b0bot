from dotenv import dotenv_values
from flask import jsonify
import json
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.schema import HumanMessage, SystemMessage, AIMessage
from langchain.output_parsers import DatetimeOutputParser
from models.NewsModel import CybernewsDB


class NewsService:
    def __init__(self) -> None:
        self.db = CybernewsDB()
        self.OPENAI_API_KEY = dotenv_values(".env").get("OPENAI_API_KEY")
        self.llm = ChatOpenAI(temperature=0.9, openai_api_key=self.OPENAI_API_KEY)

    """
    Return news without considering keywords
    """

    def getNews(self):
        # fixed format for answer
        answer_format = "title [source, date(MM/DD/YYYY)]\n"

        # fetch news data from db:
        # only fetch data with valid `author` and `newsDate`
        # drop field "id" from collection
        news_data = self.db.get_news_collections().find(
            {"author": {"$ne": "N/A"}, "newsDate": {"$ne": "N/A"}},
            {"headlines": 1, "newsDate": 1, "author": 1, "_id": 0},
        )
        news_data = list(news_data)

        # # add prompt
        # prompt = PromptTemplate(
        #     input_variables=["format", "data"],
        #     template="""
        #     {data}
        #     Please give me a list of the most recent cybersecurity news based on the news given above.
        #     Indicate the source and date.
        #     Return the answer with the format of {format}.
        #     Do not stop generating the answer until it is complete.
        #     """,
        # )

        # news = self.llm(prompt.format(format=answer_format, data=news_data))

        news = self.llm(
            [
                SystemMessage(
                    content="You are a news analyzer that will read the cyber security news given by the user and return the answer based on the user's request."
                ),
                HumanMessage(content=str(news_data)),
                AIMessage(
                    content="I have read the news you provided. Now please tell me your request."
                ),
                HumanMessage(
                    content="""Please give me a list of the most recent cybersecurity news based on the news given above.
                    Indicate the source and date.
                    Return the answers strictly with the format of {answer_format}.
                    Do not add any description to the answer.
                    Do not add bullets.
                    Do not stop generating the answer until it is complete.""".format(
                        answer_format=answer_format
                    )
                ),
            ]
        )

        print(news.content)

        # convert news data into JSON format
        news_JSON = self.toJSON(news.content)

        return news_JSON

    """
    return news based on certain keywords
    """

    def getNewsWithKeywords(self, user_keywords):
        # fixed format for answer
        answer_format = "news content (data source, date)"

        # add prompt
        prompt = PromptTemplate(
            input_variables=["keywords", "format"],
            template="""
            Please give me a list of the most recent cybersecurity news with keywords of {keywords}.
            Indicate data source and date.
            Return the answer with the format of '{format}'.
            """,
        )
        news = self.llm(prompt.format(keywords=user_keywords, format=answer_format))
        print(news)

        # convert news data into JSON format
        news_JSON = self.toJSON(news)

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
        news_list = data.split("\n")
        news_list_json = []

        for item in news_list:
            # Avoid dirty data
            if len(item) == 0:
                continue
            # Split the string at the first occurrence of '('
            title, remaining = item.split("[", 1)

            # Extract the source by splitting at ',' and removing leading/trailing whitespace
            source = remaining.split(",")[0].strip()

            # Extract the date by splitting at ',' and removing leading/trailing whitespace
            date = remaining.split(",")[1].strip().rstrip("]")

            # Create a dictionary for each news item and append it to the news_list
            news_item = {"title": title.strip(), "source": source, "date": date}
            news_list_json.append(news_item)

        return jsonify(news_list_json)
