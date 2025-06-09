# generate_alerts.py
from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

client = MongoClient(os.getenv("MONGO_URI"), tls=True, tlsAllowInvalidCertificates=True)
db = client["stock_alert"]

# 관심 이벤트 유형과 키워드 (추후 사용자별 설정으로 확장 가능)
INTERESTING_EVENTS = ["MERGER", "EARNINGS", "GUIDANCE"]
KEYWORDS = ["nvda", "rtx", "chevron", "tariff"]

alerts = []

for doc in db.news.find():
    title_lower = doc["title"].lower()
    if doc["event"] in INTERESTING_EVENTS and any(keyword in title_lower for keyword in KEYWORDS):
        alerts.append(doc)

print("🚨 알림 대상 뉴스:")
for alert in alerts:
    print(f"- [{alert['event']}] {alert['title']}")
