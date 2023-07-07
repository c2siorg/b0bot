from config.Database import client

db = client.testDB
print(db.list_collection_names())
