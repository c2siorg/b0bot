from dotenv import dotenv_values
from pymongo import MongoClient

DB_PASSWORD = dotenv_values(".env").get("DB_PASSWORD")

client = MongoClient(f"mongodb+srv://hardikgpu01:{DB_PASSWORD}@practice.pdylnhr.mongodb.net/")