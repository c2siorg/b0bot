"""
Description:

This file is for temporary use.
For now, Python package `cybernews` will be used for fetching news data from the Internet and to the database.
Once the part of API service is completed, this part (news db updating) will begin by implementing web scraping logic 
based on the code of `cybernews` pacakge.
"""

from dotenv import dotenv_values
from pymongo import MongoClient
from cybernews.cybernews import CyberNews

# MongoDB Database connection
DB_PASSWORD = dotenv_values(".env").get("DB_PASSWORD")

client = MongoClient(f"mongodb+srv://b0bot:{DB_PASSWORD}@cluster0.zqgexb4.mongodb.net/")

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

Notice: "id" should be removed before the news is inserted into the database.
"""

# db has limited storage space(512mb), clean up the old news everytime
collection.delete_many({})

# Insert all feteched news into the database.
for newsType in newsBox.keys():
    for news in newsBox[newsType]:
        news.pop("id")
        collection.insert_one(news)
