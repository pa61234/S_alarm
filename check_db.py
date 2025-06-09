from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()
client = MongoClient(os.getenv("MONGO_URI"))
db = client["stock_alert"]

print("=== 데이터베이스 상태 ===")
print(f"전체 뉴스: {db.news.count_documents({})}")
print(f"한국어 뉴스: {db.news.count_documents({'lang': 'ko'})}")
print(f"기업 관련 뉴스: {db.news.count_documents({'companies': {'$exists': True, '$ne': []}})}")

print("\n=== 최근 뉴스 5개 ===")
for n in db.news.find().sort("published", -1).limit(5):
    print(f"- {n.get('title')} | {n.get('lang')} | {n.get('companies', [])}")

print("\n=== 기업 관련 뉴스 5개 ===")
for n in db.news.find({"companies": {"$exists": True, "$ne": []}}).sort("published", -1).limit(5):
    print(f"- {n.get('title')} | {n.get('lang')} | {n.get('companies', [])}") 