from pymongo import MongoClient
from datetime import datetime

client = MongoClient("mongodb://localhost:27017")
db = client["stock_alert"]

news = db.news.find({ "lang": "ko" }).sort("published", -1).limit(3)

for item in news:
    print(f"[{item.get('published')}] {item.get('title')}")
    print(f"  📌 event: {item.get('event')} | 🏢 companies: {item.get('companies')}")
    print()

