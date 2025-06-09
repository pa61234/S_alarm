# S_alarm/remove_duplicates.py

from pymongo import MongoClient
from dotenv import load_dotenv
import os

# 환경변수 로드
load_dotenv()
client = MongoClient(os.getenv("MONGO_URI"))
db = client["stock_alert"]

# 중복 뉴스 찾기 및 삭제
pipeline = [
    {"$sort": {"published": -1}},  # 최신순 정렬
    {
        "$group": {
            "_id": {"title": "$title", "source": "$source"},
            "ids_to_keep": {"$first": "$_id"},
            "ids_to_delete": {"$push": "$_id"},
        }
    },
    {
        "$project": {
            "_id": 0,
            "ids_to_keep": 1,
            "ids_to_delete": {
                "$filter": {
                    "input": "$ids_to_delete",
                    "as": "id",
                    "cond": {"$ne": ["$$id", "$ids_to_keep"]}
                }
            }
        }
    }
]

results = list(db.news.aggregate(pipeline))
deleted_count = 0
for r in results:
    if r["ids_to_delete"]:
        result = db.news.delete_many({"_id": {"$in": r["ids_to_delete"]}})
        deleted_count += result.deleted_count

print(f"✅ 중복 뉴스 {deleted_count}건 삭제 완료")
