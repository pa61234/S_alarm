from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()
client = MongoClient(os.getenv("MONGO_URI"))
db = client["stock_alert"]

# 전체 뉴스 수 확인
total_news = db.news.count_documents({})
print(f"전체 뉴스 수: {total_news}")

# 한국어 뉴스 수 확인
ko_news = db.news.count_documents({"lang": "ko"})
print(f"한국어 뉴스 수: {ko_news}")

# 최근 뉴스 3개 출력
print("\n최근 뉴스 3개:")
for news in db.news.find({"lang": "ko"}).sort("published", -1).limit(3):
    print(f"\n제목: {news.get('title', 'N/A')}")
    print(f"발행일: {news.get('published', 'N/A')}")
    print(f"언어: {news.get('lang', 'N/A')}")
    print(f"회사: {news.get('companies', [])}")
    print(f"이벤트: {news.get('event', 'N/A')}") 