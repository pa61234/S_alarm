from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")
db = client["stock_alert"]

latest = db.news.find_one({"lang": "ko"}, sort=[("published", -1)])

if latest:
    print(f"가장 최근 뉴스 _id: {latest['_id']}")
else:
    print("뉴스 데이터가 없습니다.") 