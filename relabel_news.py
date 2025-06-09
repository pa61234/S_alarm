from pymongo import MongoClient
from dotenv import load_dotenv
import os
import re

load_dotenv()

client = MongoClient(os.getenv("MONGO_URI"), tls=True, tlsAllowInvalidCertificates=True)
db = client["stock_alert"]

def extract_company(title: str) -> str:
    match = re.search(r"\(([^)]+)\)", title)
    if match:
        return match.group(1).upper()
    return title.split()[0].capitalize()

# 모든 뉴스 문서를 순회하며 company 필드 업데이트
news_items = db.news.find()
for item in news_items:
    company = extract_company(item["title"])
    db.news.update_one({"_id": item["_id"]}, {"$set": {"company": company}})

print("✅ 모든 뉴스 문서에 company 필드 업데이트 완료")
