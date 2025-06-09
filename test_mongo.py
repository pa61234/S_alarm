from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

# MongoDB URI 출력 (비밀번호는 마스킹)
mongo_uri = os.getenv("MONGO_URI")
if mongo_uri:
    masked_uri = mongo_uri.replace(mongo_uri.split("@")[0], "***")
    print(f"MongoDB URI: {masked_uri}")
else:
    print("MongoDB URI가 설정되지 않았습니다.")

# MongoDB 연결 테스트
try:
    client = MongoClient(os.getenv("MONGO_URI"))
    db = client["stock_alert"]
    
    # 데이터베이스 연결 테스트
    print("\n데이터베이스 연결 테스트:")
    print(f"데이터베이스 목록: {client.list_database_names()}")
    
    # 컬렉션 확인
    print(f"\n컬렉션 목록: {db.list_collection_names()}")
    
    # 뉴스 데이터 확인
    news_count = db.news.count_documents({})
    print(f"\n전체 뉴스 수: {news_count}")
    
    # 한국어 뉴스 확인
    ko_news = list(db.news.find({"lang": "ko"}).limit(1))
    if ko_news:
        print("\n한국어 뉴스 샘플:")
        print(ko_news[0])
    else:
        print("\n한국어 뉴스가 없습니다.")
        
except Exception as e:
    print(f"\n오류 발생: {str(e)}")
