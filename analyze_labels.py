from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

client = MongoClient(os.getenv("MONGO_URI"), tls=True, tlsAllowInvalidCertificates=True)
db = client["stock_alert"]

pipeline = [
    {
        "$group": {
            "_id": "$event",
            "count": {"$sum": 1}
        }
    },
    {
        "$sort": {"count": -1}
    }
]

results = db.news.aggregate(pipeline)

print("📊 라벨별 뉴스 개수:")
for result in results:
    print(f"{result['_id']}: {result['count']}")
