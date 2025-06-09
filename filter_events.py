from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

client = MongoClient(os.getenv("MONGO_URI"), tls=True, tlsAllowInvalidCertificates=True)
db = client["stock_alert"]

# 관심 있는 이벤트 유형만 필터링
TARGET_EVENTS = ["MERGER", "EARNINGS", "LABOR"]

filtered_news = db.news.find({"event": {"$in": TARGET_EVENTS}}).sort("published", -1)

print("🔔 필터링된 뉴스 목록:")
for news in filtered_news:
    print(f"[{news['event']}] {news['title']} ({news['published'].isoformat()})")
