"""
Description:

This file is for temporary use.
For now, Python package `cybernews` will be used for fetching news data from the Internet and to the database.
Once the part of API service is completed, this part (news db updating) will begin by implementing web scraping logic 
based on the code of `cybernews` pacakge.
"""
import sys
import os
from dotenv import dotenv_values
from pymongo import MongoClient
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from cybernews.CyberNews import CyberNews

# MongoDB Database connection
DB_PASSWORD = dotenv_values(".env").get("DB_PASSWORD")

client = MongoClient(f"mongodb+srv://hardikgpu01:{DB_PASSWORD}@practice.pdylnhr.mongodb.net/")
db = client.CybernewsDB

collection = db.get_collection("news")

# Different types of news
news = CyberNews()

newsBox = dict()

newsBox["general_news"] = news.get_news("general")

newsBox["cyber_attack_news"] = news.get_news("cyberAttack")

newsBox["vulnerability_news"] = news.get_news("vulnerability")

newsBox["malware_news"] = news.get_news("malware")

newsBox["security_news"] = news.get_news("security")

newsBox["data_breach_news"] = news.get_news("dataBreach")   


"""
News Format:

news = {
    "id: ""
    "headlines": "",
    "author": "",
    "fullNews": "",
    "newsURL": "",
    "newsImgURL": "",
    "newsDate": "",
}

Notice: "id" should be removed before the news is inserted into the database. newsImgURL also not important right now.
"""

# db has limited storage space(512mb), clean up old news before fetching new news.
collection.delete_many({})

# Insert all feteched news into the database.
for newsType in newsBox.keys():
    for news in newsBox[newsType]:
        news.pop("id")
        news.pop("newsImgURL")
        collection.insert_one(news)
