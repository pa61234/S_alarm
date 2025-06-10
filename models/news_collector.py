import os
import requests
from datetime import datetime, timezone, timedelta
from langdetect import detect
from models.ner import extract_companies
from models.event_classifier import classify_event
from models.sentiment_analyzer import sentiment_analyzer
from models.database import Database
from models.sentiment_analyzer import SentimentAnalyzer
import logging

logger = logging.getLogger(__name__)

class NaverNewsCollector:
    def __init__(self):
        self.client_id = os.getenv("NAVER_CLIENT_ID")
        self.client_secret = os.getenv("NAVER_CLIENT_SECRET")
        self.base_url = "https://openapi.naver.com/v1/search/news.json"
        self.sentiment_analyzer = SentimentAnalyzer()
        self.excluded_keywords = {
            '스포츠', '야구', '축구', '농구', '골프', '테니스', '배구', '홈런', '이닝', '득점',
            '승리', '패배', '경기', '선수', '감독', '팀', '리그', '시즌', '경기장', '스코어',
            '투수', '타자', '타격', '수비', '공격', '수비', '포수', '내야수', '외야수', '주자',
            '볼넷', '삼진', '안타', '홈런', '타점', '득점', '도루', '실책', '보크', '폭투'
        }
        
    def is_sports_news(self, title, content):
        """스포츠 뉴스 여부를 확인"""
        text = (title + ' ' + content).lower()
        return any(keyword in text for keyword in self.excluded_keywords)

    def collect_news(self, db):
        """네이버 뉴스 API를 통해 뉴스를 수집하고 DB에 저장"""
        headers = {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret
        }
        
        # 하루 전 00시 기준 시간 계산
        now = datetime.now(timezone(timedelta(hours=9)))
        yesterday_midnight = datetime(now.year, now.month, now.day, 0, 0, 0, tzinfo=timezone(timedelta(hours=9))) - timedelta(days=1)
        
        # 검색어 목록 (주요 기업들)
        search_queries = [
            "삼성전자", "SK하이닉스", "LG에너지솔루션", "현대차", "기아",
            "NAVER", "카카오", "LG전자", "POSCO홀딩스", "삼성바이오로직스",
            "삼성SDI", "LG화학", "SK이노베이션", "SK텔레콤", "KT",
            "삼성생명", "KB금융", "신한지주", "하나금융지주", "우리금융지주"
        ]
        
        for query in search_queries:
            try:
                params = {
                    "query": query,
                    "display": 100,  # 최대 100개 결과
                    "sort": "date"   # 최신순
                }
                
                response = requests.get(self.base_url, headers=headers, params=params)
                response.raise_for_status()
                
                news_items = response.json()["items"]
                
                for item in news_items:
                    title = item["title"].replace("&quot;", "").replace("&apos;", "").replace("&amp;", "&")
                    link = item["link"]
                    
                    # 스포츠 뉴스 제외
                    if self.is_sports_news(title, item["description"]):
                        logger.info(f"스포츠 뉴스 제외: {title}")
                        continue
                    
                    # 중복 확인
                    if db.news.find_one({"title": title}):
                        continue
                    
                    # 시간 파싱
                    pub_date = item["pubDate"]
                    published_dt = datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S %z")
                    if published_dt.tzinfo.utcoffset(published_dt) != timedelta(hours=9):
                        published_dt = published_dt.astimezone(timezone(timedelta(hours=9)))
                    
                    # 하루 전 00시 이전의 뉴스는 건너뛰기
                    if published_dt < yesterday_midnight:
                        continue
                    
                    # 언어 감지
                    try:
                        lang = detect(title)
                    except:
                        lang = "unknown"
                    
                    # 기본 저장 구조
                    doc = {
                        "title": title,
                        "link": link,
                        "published": published_dt,
                        "source": "네이버뉴스",
                        "lang": lang,
                    }
                    
                    # 한국어 뉴스인 경우 추가 분석
                    if lang == "ko":
                        companies = extract_companies(title)
                        if companies:
                            doc.update({
                                "companies": companies,
                                "event": classify_event(title),
                                "sentiment": self.sentiment_analyzer.analyze(title),
                                "analyzed": True
                            })
                    
                    db.news.insert_one(doc)
                    print(f"새 뉴스 추가: {title}")
                    
            except Exception as e:
                print(f"{query} 검색 중 오류: {str(e)}")
                continue 