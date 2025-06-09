from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

client = MongoClient(os.getenv("MONGO_URI"), tls=True, tlsAllowInvalidCertificates=True)
db = client["stock_alert"]

# 간단한 티커-업종 매핑
TICKER_INDUSTRY_MAP = {
    "NVDA": "Semiconductors",
    "AAPL": "Consumer Electronics",
    "MSFT": "Software",
    "TSLA": "Automobiles",
    "GOOG": "Internet Services",
    "AMZN": "E-commerce",
    "META": "Social Media",
    "INTC": "Semiconductors",
    "NFLX": "Streaming Services",
    "JPM": "Banking",
    "BAC": "Banking",
    "WMT": "Retail"
}

news_items = db.news.find()
for item in news_items:
    ticker = item.get("company")
    if not ticker:
        continue

    industry = TICKER_INDUSTRY_MAP.get(ticker)
    if industry:
        db.news.update_one({"_id": item["_id"]}, {"$set": {"industry": industry}})

print("✅ 업종 정보 업데이트 완료")
