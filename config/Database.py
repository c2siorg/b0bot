from dotenv import dotenv_values
from pymongo import MongoClient

DB_PASSWORD = dotenv_values(".env").get("DB_PASSWORD")

client = MongoClient(f"mongodb+srv://b0bot:{DB_PASSWORD}@cluster0.zqgexb4.mongodb.net/")
