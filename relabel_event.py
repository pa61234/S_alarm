import re
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import datetime

# .env 파일에서 MONGO_URI 로드
load_dotenv()
client = MongoClient(os.getenv("MONGO_URI"), tls=True, tlsAllowInvalidCertificates=True)
db = client["stock_alert"]
collection = db.news

# 이벤트 키워드 사전 (카테고리: 키워드 리스트)
EVENT_KEYWORDS = {
    "EARNINGS": ["earnings", "results", "eps", "quarter", "q1", "q2", "q3", "q4"],
    "GUIDANCE": ["guidance", "forecast", "outlook", "raises", "cuts", "profit warning"],
    "MERGER": ["merger", "acquisition", "deal", "buyout", "takeover", "combination", "merge"],
    "POLICY": ["tariff", "regulation", "ruling", "law", "biden", "trump", "court", "fed", "policy"],
    "PRODUCT": ["launch", "product", "release", "unveil", "introduce", "announcement"],
    "LABOR": ["strike", "union", "layoff", "labor", "workers", "walkout", "hiring"],
    "INVESTMENT": ["invest", "investment", "backing", "funding", "raise", "capital", "venture"],
    "SECURITY": ["breach", "hack", "cyberattack", "security", "data leak"],
    "LEGAL": ["lawsuit", "court", "settlement", "antitrust", "sues", "investigation", "probe"],
    "SUSPENSION": ["halt", "pause", "suspend", "shutdown", "close", "bankruptcy", "insolvency"]
}

def detect_event(text: str) -> str:
    text = text.lower()
    for event, keywords in EVENT_KEYWORDS.items():
        for kw in keywords:
            if re.search(r'\b' + re.escape(kw) + r'\b', text):
                return event
    return "OTHER"

# 뉴스 문서 전체 업데이트
count = 0
for doc in collection.find():
    title = doc.get("title", "")
    new_event = detect_event(title)
    if new_event != doc.get("event"):
        collection.update_one({"_id": doc["_id"]}, {"$set": {"event": new_event}})
        count += 1

print(f"[{datetime.datetime.now()}] 이벤트 라벨링 업데이트 완료: {count}건 수정됨.")
