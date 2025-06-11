# S_alarm/app.py

from flask import Flask, render_template, request, jsonify, session
from pymongo import MongoClient
from dotenv import load_dotenv
import os
from bson import ObjectId
from datetime import datetime, timezone, timedelta
import json
import subprocess
import sys
import uuid
import logging
from logging.handlers import RotatingFileHandler
import re

from models.ner import extract_companies
from models.event_classifier import classify_event
from models.sentiment_analyzer import sentiment_analyzer
from models.news_collector import NaverNewsCollector

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
handler = RotatingFileHandler('app.log', maxBytes=10000000, backupCount=5)
handler.setFormatter(logging.Formatter(
    '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
))
logger.addHandler(handler)

load_dotenv()
client = MongoClient(os.getenv("MONGO_URI"))
db = client["stock_alert"]

app = Flask(__name__)
app.secret_key = os.urandom(24)  # 세션을 위한 시크릿 키

# 산업군 매핑 로드 (앱 시작 시 1회만)
with open("sector_mapping.json", "r", encoding="utf-8") as f:
    SECTOR_MAP = json.load(f)

# 유니크한 산업군 리스트
sectors = sorted(list(set(SECTOR_MAP.values())))

# 뉴스 캐시를 저장할 전역 변수
news_cache = {}
CACHE_EXPIRY = timedelta(hours=1)  # 캐시 만료 시간

def cleanup_expired_cache():
    """만료된 캐시를 정리하는 함수"""
    now = datetime.now()
    expired_sessions = []
    
    for session_id, cache_data in news_cache.items():
        if 'last_accessed' not in cache_data:
            expired_sessions.append(session_id)
            continue
            
        if now - cache_data['last_accessed'] > CACHE_EXPIRY:
            expired_sessions.append(session_id)
    
    for session_id in expired_sessions:
        del news_cache[session_id]
        logger.info(f"만료된 캐시 정리: {session_id}")

def get_elapsed_time(published_time):
    """뉴스 게시 시간으로부터의 경과시간을 계산"""
    now = datetime.now(timezone(timedelta(hours=9)))  # KST 기준 현재 시간
    
    # published_time이 naive datetime인 경우 KST로 변환
    if published_time.tzinfo is None:
        published_time = published_time.replace(tzinfo=timezone(timedelta(hours=9)))
    # published_time이 다른 timezone인 경우 KST로 변환
    elif published_time.tzinfo.utcoffset(published_time) != timedelta(hours=9):
        published_time = published_time.astimezone(timezone(timedelta(hours=9)))
    
    diff = now - published_time
    
    if diff.days > 0:
        return '+1day'
    elif diff.seconds >= 21600:  # 6시간
        return '+6hours'
    elif diff.seconds >= 10800:  # 3시간
        return '+3hours'
    elif diff.seconds >= 3600:  # 1시간
        return '+1hour'
    else:
        return 'New'

def clean_html_tags(text):
    """HTML 태그를 제거하는 함수"""
    if not text:
        return text
    # <b> 태그 제거
    text = re.sub(r'<b>|</b>', '', text)
    # 다른 HTML 태그도 제거
    text = re.sub(r'<[^>]+>', '', text)
    return text

def prepare_news(query, skip=0, limit=30):
    """뉴스를 준비하는 함수"""
    try:
        # 스포츠 관련 키워드
        sports_keywords = ['스포츠', '축구', '야구', '농구', '골프', '테니스', '올림픽', '월드컵', 'K리그', 'KBO', 'KBL']
        
        # DB에서 뉴스 가져오기
        news = list(db.news.find(query).sort("published", -1).skip(skip).limit(limit * 2))  # 스포츠 뉴스 제외를 위해 더 많은 뉴스를 가져옴
        
        # 데이터 처리
        processed_news = []
        for item in news:
            try:
                # 스포츠 뉴스 제외
                title = item.get('title', '')
                if any(keyword in title for keyword in sports_keywords):
                    continue
                
                item['_id'] = str(item['_id'])
                
                # 시간 처리
                published_time = item['published']
                if published_time.tzinfo is None:
                    # UTC 시간을 KST로 변환
                    published_time = published_time.replace(tzinfo=timezone.utc).astimezone(timezone(timedelta(hours=9)))
                elif published_time.tzinfo.utcoffset(published_time) != timedelta(hours=9):
                    # 다른 timezone을 KST로 변환
                    published_time = published_time.astimezone(timezone(timedelta(hours=9)))
                
                item['published'] = published_time
                item['url'] = item.get('link', '#')
                item['elapsed_time'] = get_elapsed_time(published_time)
                item['sentiment'] = item.get('sentiment', 'unknown')
                # HTML 태그 제거
                item['title'] = clean_html_tags(title)
                
                processed_news.append(item)
                
                # 필요한 만큼의 뉴스만 처리
                if len(processed_news) >= limit:
                    break
                    
            except Exception as e:
                logger.error(f"뉴스 데이터 처리 실패: {item.get('title', 'unknown')} - {str(e)}", exc_info=True)
                continue
        
        return processed_news
    except Exception as e:
        logger.error(f"뉴스 준비 중 오류 발생: {str(e)}", exc_info=True)
        raise

@app.route("/", methods=["GET"])
def index():
    try:
        # 서버가 실행 중인지 확인하고 필요시 시작
        if sys.platform == 'win32':
            result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True)
            if '8000' not in result.stdout:
                python_exe = sys.executable
                subprocess.Popen([python_exe, 'app.py'], 
                               creationflags=subprocess.CREATE_NEW_CONSOLE,
                               stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL)
                return "서버를 시작합니다. 잠시 후 다시 시도해주세요.", 503
        else:
            result = subprocess.run(['lsof', '-i', ':8000'], capture_output=True, text=True)
            if not result.stdout:
                subprocess.Popen(['python3', 'app.py'],
                               stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL)
                return "서버를 시작합니다. 잠시 후 다시 시도해주세요.", 503

        selected_sector = request.args.get("sector", "")
        keyword = request.args.get("keyword", "")
        
        # 새로운 뉴스 수집
        logger.info("새로운 뉴스 수집 시작...")
        news_collector = NaverNewsCollector()
        news_collector.collect_news(db)
        
        # 1. 기업 정보가 있는 뉴스만 가져옴
        query = {"companies": {"$exists": True, "$ne": []}}
        if selected_sector:
            query["companies"] = {"$in": [c for c, s in SECTOR_MAP.items() if s == selected_sector]}
        
        # 세션 ID 생성 또는 가져오기
        if 'session_id' not in session:
            session['session_id'] = str(uuid.uuid4())
        
        # 30개의 뉴스 준비
        prepared_news = prepare_news(query, limit=30)
        
        # 키워드 필터링
        if keyword:
            prepared_news = [item for item in prepared_news if keyword in item["title"]]
        
        # 캐시에 저장
        news_cache[session['session_id']] = {
            'news': prepared_news,
            'current_index': 0,
            'query': query,
            'last_accessed': datetime.now()
        }
        
        return render_template('index.html', 
                             news=prepared_news[:30],
                             sectors=sectors,
                             selected_sector=selected_sector,
                             keyword=keyword)
    except Exception as e:
        logger.error(f"인덱스 페이지 로딩 중 오류 발생: {str(e)}", exc_info=True)
        return "서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요.", 500

@app.route("/load_more", methods=["POST"])
def load_more():
    try:
        if 'session_id' not in session:
            logger.warning("세션 ID가 없는 요청")
            return jsonify({"status": "error", "message": "세션이 만료되었습니다"}), 400
        
        session_id = session['session_id']
        if session_id not in news_cache:
            logger.warning(f"캐시가 없는 세션 ID: {session_id}")
            return jsonify({"status": "error", "message": "캐시가 만료되었습니다"}), 400
        
        cache = news_cache[session_id]
        current_index = cache['current_index']
        
        # 마지막 접근 시간 업데이트
        cache['last_accessed'] = datetime.now()
        
        # 다음 10개 뉴스 반환
        next_news = cache['news'][current_index:current_index + 10]
        cache['current_index'] += 10
        
        # 새로운 10개 뉴스 준비
        if current_index + 10 >= len(cache['news']):
            new_news = prepare_news(cache['query'], 
                                  skip=len(cache['news']), 
                                  limit=10)
            if cache['keyword']:
                new_news = [item for item in new_news if cache['keyword'] in item["title"]]
            cache['news'].extend(new_news)
        
        return jsonify({
            "status": "success",
            "news": next_news,
            "has_more": len(cache['news']) > cache['current_index']
        })
    except Exception as e:
        logger.error(f"더보기 요청 처리 중 오류 발생: {str(e)}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.json
    news_id = data.get("news_id")
    title = data.get("title")

    if not news_id or not title:
        return jsonify({"status": "error", "message": "뉴스 ID와 제목이 필요합니다"}), 400

    try:
        companies = extract_companies(title)
        event = classify_event(title)

        # 산업군 추출
        sector = ""
        for company in companies:
            if company in SECTOR_MAP:
                sector = SECTOR_MAP[company]
                break

        db.news.update_one(
            {"_id": ObjectId(news_id)},
            {"$set": {
                "companies": companies,
                "event": event,
                "sector": sector,
                "analyzed": True
            }}
        )

        return jsonify({"status": "success", "message": "뉴스 분석이 완료되었습니다"})
    except Exception as e:
        error_msg = f"뉴스 분석 실패: {str(e)}"
        print(f"[ERROR] {error_msg}")
        return jsonify({"status": "error", "message": error_msg}), 500

@app.route("/feedback", methods=["POST"])
def feedback():
    data = request.json
    news_id = data.get("news_id")
    feedback = data.get("feedback")

    if not news_id or not feedback:
        return jsonify({"status": "error", "message": "뉴스 ID와 피드백이 필요합니다"}), 400

    try:
        db.feedback.insert_one({
            "news_id": ObjectId(news_id),
            "feedback": feedback,
            "timestamp": datetime.utcnow()
        })
        return jsonify({"status": "success", "message": "피드백이 저장되었습니다"})
    except Exception as e:
        error_msg = f"피드백 저장 실패: {str(e)}"
        print(f"[ERROR] {error_msg}")
        return jsonify({"status": "error", "message": error_msg}), 500

if __name__ == "__main__":
    import threading
    import webbrowser
    import time
    
    def open_browser():
        time.sleep(1.5)  # 서버가 완전히 시작될 때까지 잠시 대기
        webbrowser.open('http://127.0.0.1:8000')
    
    # 브라우저를 별도 스레드에서 열기
    threading.Thread(target=open_browser).start()
    
    # 서버 시작
    app.run(host='0.0.0.0', port=8000, debug=True, use_reloader=False) 