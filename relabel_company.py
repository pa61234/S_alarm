# S_alarm/relabel_company.py

import re
from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

client = MongoClient(os.getenv("MONGO_URI"), tls=True, tlsAllowInvalidCertificates=True)
db = client["stock_alert"]
collection = db.news

# 의미 없는 단어 리스트 (전부 소문자로!)
EXCLUDE_KEYWORDS = {
    "stock", "stocks", "shares", "earnings", "revenue", "guidance", "forecast",
    "report", "market", "price", "target", "deal", "merger", "ipo", "dividend",
    "update", "company", "inc", "corp", "group", "fund", "etf", "qqq", "spy", "dia",
    "nasdaq", "dow", "s&p", "turn", "fall", "rise", "oil", "gold", "court", "tariff", "trump",
    "today", "live", "review", "bank", "financial", "business", "tech", "technology"
}

def extract_company(title: str) -> str:
    title = title.strip()

    # 괄호 속 티커
    match = re.search(r"\(([^)]+)\)", title)
    if match:
        return match.group(1).upper()

    # 전치사 뒤 티커 (After 등)
    match = re.search(r"\b(After|Following|As|When|While|Because|Since|If)\s+([A-Z]{2,5})\b", title)
    if match and match.group(2).isalpha():
        return match.group(2).upper()

    # 제목 내에서 대문자 티커 유추
    words = title.split()
    for word in words[1:]:  # 첫 단어 제외
        clean = re.sub(r"[^A-Za-z]", "", word).lower()
        if clean in EXCLUDE_KEYWORDS or len(clean) < 2:
            continue
        if word.isupper() and 2 <= len(word) <= 5:
            return word.upper()
        if word.istitle() and clean not in EXCLUDE_KEYWORDS:
            return word.capitalize()

    return "UNKNOWN"

# 뉴스 항목 전체에 적용
def relabel_all():
    news_items = list(collection.find())
    updated_count = 0

    for item in news_items:
        title = item.get("title", "")
        current_company = item.get("company", "")
        new_company = extract_company(title)

        if new_company != current_company:
            collection.update_one(
                {"_id": item["_id"]},
                {"$set": {"company": new_company}}
            )
            updated_count += 1

    print(f"🔁 라벨링 완료: {updated_count}건 수정됨")

if __name__ == "__main__":
    relabel_all()
