from pymongo import MongoClient
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

# 환경 변수 로드
load_dotenv()

# MongoDB 연결
client = MongoClient(os.getenv("MONGO_URI"))
db = client["stock_alert"]

print("MongoDB 연결 성공")

# 테스트용 뉴스 데이터
test_news = [
    {
        "title": "삼성전자, AI 반도체 시장 공략 강화...신규 투자 발표",
        "content": "삼성전자가 AI 반도체 시장 공략을 위해 대규모 투자 계획을 발표했습니다...",
        "published": datetime.now() - timedelta(hours=1),
        "lang": "ko",
        "event": "투자",
        "companies": ["삼성전자"]
    },
    {
        "title": "SK하이닉스, HBM 생산능력 2배 확대...AI 수요 대응",
        "content": "SK하이닉스가 AI 수요 증가에 대응하기 위해 HBM 생산능력을 확대하기로 했습니다...",
        "published": datetime.now() - timedelta(hours=2),
        "lang": "ko",
        "event": "생산",
        "companies": ["SK하이닉스"]
    },
    {
        "title": "네이버, 클라우드 사업부문 분할 검토...주가 상승",
        "content": "네이버가 클라우드 사업부문의 분할을 검토 중이라는 소식에 주가가 상승했습니다...",
        "published": datetime.now() - timedelta(hours=3),
        "lang": "ko",
        "event": "기업구조조정",
        "companies": ["네이버"]
    }
]

# 기존 데이터 삭제 (테스트를 위해)
print("기존 한국어 뉴스 삭제 중...")
result = db.news.delete_many({"lang": "ko"})
print(f"삭제된 뉴스 수: {result.deleted_count}")

# 새 데이터 추가
print("\n새 뉴스 데이터 추가 중...")
result = db.news.insert_many(test_news)
print(f"추가된 뉴스 데이터 수: {len(result.inserted_ids)}")

# 추가된 데이터 확인
print("\n추가된 뉴스 목록:")
for news in db.news.find({"lang": "ko"}).sort("published", -1):
    print(f"\n[{news['published']}] {news['title']}")
    print(f"  📌 event: {news['event']} | 🏢 companies: {news['companies']}")

# 전체 뉴스 수 확인
total_news = db.news.count_documents({})
ko_news = db.news.count_documents({"lang": "ko"})
print(f"\n전체 뉴스 수: {total_news}")
print(f"한국어 뉴스 수: {ko_news}") 