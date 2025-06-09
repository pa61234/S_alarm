from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()
client = MongoClient(os.getenv("MONGO_URI"))
db = client["stock_alert"]

# 예시 기사 제거
example_titles = [
    "삼성전자, AI 반도체 시장 공략 강화...신규 투자 발표",
    "SK하이닉스, HBM 생산능력 2배 확대...AI 수요 대응",
    "네이버, 클라우드 사업부문 분할 검토...주가 상승"
]

# 1. 정확한 제목으로 제거
result1 = db.news.delete_many({"title": {"$in": example_titles}})
print(f"정확한 제목으로 제거된 기사 수: {result1.deleted_count}")

# 2. 부분 일치로 제거
for title in example_titles:
    result2 = db.news.delete_many({"title": {"$regex": title.split("...")[0]}})
    print(f"'{title.split('...')[0]}' 포함 기사 제거 수: {result2.deleted_count}")

# 3. 예시 기사와 유사한 패턴의 기사 제거
result3 = db.news.delete_many({
    "title": {
        "$regex": ".*(삼성전자|SK하이닉스|네이버).*(AI|반도체|HBM|클라우드).*"
    }
})
print(f"유사 패턴 기사 제거 수: {result3.deleted_count}")

# 현재 데이터베이스 상태 출력
print("\n=== 현재 데이터베이스 상태 ===")
print(f"전체 뉴스: {db.news.count_documents({})}")
print(f"한국어 뉴스: {db.news.count_documents({'lang': 'ko'})}")
print(f"기업 관련 뉴스: {db.news.count_documents({'companies': {'$exists': True, '$ne': []}})}")

print("\n=== 기업 관련 뉴스 목록 ===")
for n in db.news.find({"companies": {"$exists": True, "$ne": []}}).sort("published", -1):
    print(f"- {n.get('title')} | {n.get('lang')} | {n.get('companies', [])}") 