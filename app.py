# S_alarm/app.py

from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from dotenv import load_dotenv
import os
from bson import ObjectId
from datetime import datetime, timezone, timedelta
import json
import feedparser
from langdetect import detect
import subprocess

from models.ner import extract_companies
from models.event_classifier import classify_event
from models.sentiment_analyzer import sentiment_analyzer

load_dotenv()
client = MongoClient(os.getenv("MONGO_URI"))
db = client["stock_alert"]

app = Flask(__name__)

# RSS 피드 목록
RSS_FEEDS = {
    "조선비즈": "https://biz.chosun.com/rss.xml",
    "머니투데이": "https://news.mt.co.kr/mtview/rss.htm",
    "한국경제": "https://www.hankyung.com/feed/news",
    "서울경제": "https://www.sedaily.com/rss/Finance.xml",
    "매일경제": "https://www.mk.co.kr/rss/30000001/",
    "아시아경제": "https://www.asiae.co.kr/rss/news.xml",
    "이데일리": "https://rss.edaily.co.kr/rss/Sec_list.xml",
    "전자신문": "https://rss.etnews.com/ETnews.xml",
    "ZDNet Korea": "https://zdnet.co.kr/news/news.xml",
    "디지털타임스": "https://www.dt.co.kr/rss/news.xml",
    "연합뉴스": "https://www.yna.co.kr/news/rss",
    "KDI뉴스": "https://www.kdi.re.kr/rss/kdi_news.xml",
    "파이낸셜뉴스": "https://www.fnnews.com/rss/fn_realnews_finance.xml",
    "헤럴드경제": "https://biz.heraldcorp.com/common/rss_xml.php?ct=010000000000",
    "MTN": "https://news.mtn.co.kr/newscenter/rss/news.xml",
    "한국투자증권": "https://www.koreainvestment.com/rss/news.xml",
    "NH투자증권": "https://www.nhqv.com/rss/news.xml",
    "KB증권": "https://www.kbsec.com/rss/news.xml",
    "신한투자증권": "https://www.shinhan.com/rss/news.xml",
    "디지털데일리": "https://www.digitaldaily.co.kr/rss/news.xml",
    "테크M": "https://www.techm.kr/rss/news.xml",
    "아이뉴스24": "https://www.inews24.com/rss/news.xml",
    "바이오스펙테이터": "https://www.biospectator.com/rss/news.xml",
    "팜뉴스": "https://www.pharmnews.com/rss/allArticle.xml",
    "식품저널": "https://www.foodnews.co.kr/rss/allArticle.xml",
    "파이낸셜뉴스 산업": "https://www.fnnews.com/rss/fn_industry.xml",
    "전자신문 산업": "https://rss.etnews.com/ETnews_industry.xml"
}

# 산업군 매핑 로드 (앱 시작 시 1회만)
with open("sector_mapping.json", "r", encoding="utf-8") as f:
    SECTOR_MAP = json.load(f)

# 유니크한 산업군 리스트
sectors = sorted(list(set(SECTOR_MAP.values())))

def get_elapsed_time(published_time):
    """뉴스 게시 시간으로부터의 경과시간을 계산"""
    now = datetime.now(timezone(timedelta(hours=9)))
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

@app.route("/", methods=["GET"])
def index():
    try:
        # 서버가 실행 중인지 확인하고 필요시 시작
        result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True)
        if '8000' not in result.stdout:
            subprocess.Popen(['python', 'start_server.py'], 
                           stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL)
            return "서버를 시작합니다. 잠시 후 다시 시도해주세요.", 503

        selected_sector = request.args.get("sector", "")
        keyword = request.args.get("keyword", "")
        
        # 새로운 뉴스 수집
        print("🔄 새로운 뉴스 수집 시작...")
        for source_name, feed_url in RSS_FEEDS.items():
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries:
                    title = entry.title
                    link = entry.link
                    
                    # 중복 확인
                    if db.news.find_one({"title": title, "source": source_name}):
                        continue
                    
                    # 시간 파싱
                    published = entry.get("published", "")
                    published_dt = None
                    
                    # 다양한 시간 형식 처리
                    time_formats = [
                        "%a, %d %b %Y %H:%M:%S %z",
                        "%a, %d %b %Y %H:%M:%S %Z",
                        "%Y-%m-%dT%H:%M:%S%z",
                        "%Y-%m-%d %H:%M:%S",
                    ]
                    
                    for fmt in time_formats:
                        try:
                            published_dt = datetime.strptime(published, fmt)
                            if published_dt.tzinfo is None:
                                published_dt = published_dt.replace(tzinfo=timezone(timedelta(hours=9)))
                            elif published_dt.tzinfo.utcoffset(published_dt) != timedelta(hours=9):
                                published_dt = published_dt.astimezone(timezone(timedelta(hours=9)))
                            break
                        except ValueError:
                            continue
                    
                    if not published_dt:
                        published_dt = datetime.now(timezone(timedelta(hours=9)))
                    
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
                        "source": source_name,
                        "lang": lang,
                    }
                    
                    # 한국어 뉴스인 경우 추가 분석
                    if lang == "ko":
                        companies = extract_companies(title)
                        if companies:
                            doc.update({
                                "companies": companies,
                                "event": classify_event(title),
                                "sentiment": sentiment_analyzer.analyze(title),
                                "analyzed": True
                            })
                    
                    db.news.insert_one(doc)
                    print(f"✅ 새 뉴스 추가: {title}")
                    
            except Exception as e:
                print(f"⚠️ {source_name} 피드 처리 중 오류: {str(e)}")
                continue
        
        # 1. 기업 정보가 있는 뉴스만 가져옴
        query = {"companies": {"$exists": True, "$ne": []}}
        if selected_sector:
            query["companies"] = {"$in": [c for c, s in SECTOR_MAP.items() if s == selected_sector]}
        news = list(db.news.find(query).sort("published", -1).limit(50))  # 최근 50개로 제한
        
        # 2. 키워드 필터링
        if keyword:
            news = [item for item in news if keyword in item["title"]]
        
        # 3. 기업 정보가 없는 뉴스 중에서 한국어 뉴스를 가져와서 기업 정보 추출
        if len(news) < 10:  # 기업 정보가 있는 뉴스가 10개 미만인 경우
            # 더 많은 뉴스를 가져오도록 limit 증가
            additional_news = list(db.news.find({
                "lang": "ko",
                "companies": {"$exists": False}  # companies 필드가 없는 경우
            }).sort("published", -1).limit(50))
            
            for item in additional_news:
                # 기업명 추출
                companies = extract_companies(item['title'])
                if companies:  # 기업명이 추출된 경우에만 추가
                    item['companies'] = companies
                    item['event'] = classify_event(item['title'])
                    item['sentiment'] = sentiment_analyzer.analyze(item['title'])
                    news.append(item)
                    
                    # DB에 업데이트
                    db.news.update_one(
                        {"_id": item['_id']},
                        {"$set": {
                            "companies": companies,
                            "event": item['event'],
                            "sentiment": item['sentiment'],
                            "analyzed": True
                        }}
                    )
                
                # 10개 이상이면 중단
                if len(news) >= 10:
                    break
        
        print(f"[DEBUG] 가져온 뉴스 수: {len(news)}")
        print(f"[DEBUG] 전체 뉴스 수: {db.news.count_documents({})}")
        print(f"[DEBUG] 한국어 뉴스 수: {db.news.count_documents({'lang': 'ko'})}")
        print(f"[DEBUG] 기업 관련 뉴스 수: {db.news.count_documents({'companies': {'$exists': True, '$ne': []}})}")
        
        for n in news:
            print(f"[DEBUG] 뉴스: {n['title']} | {n.get('lang', 'unknown')} | {n.get('companies', [])}")
            
        for item in news:
            item['_id'] = str(item['_id'])  # ObjectId를 문자열로 변환
            # published를 KST로 변환
            if item['published'].tzinfo is None:
                item['published'] = item['published'].replace(tzinfo=timezone(timedelta(hours=9)))
            elif item['published'].tzinfo.utcoffset(item['published']) != timedelta(hours=9):
                item['published'] = item['published'].astimezone(timezone(timedelta(hours=9)))
            # link 필드를 url로 매핑
            item['url'] = item.get('link', '#')
            # 경과시간 계산
            item['elapsed_time'] = get_elapsed_time(item['published'])
            # 감성분석 결과 추가
            item['sentiment'] = item.get('sentiment', 'unknown')
        return render_template("index.html", news=news, sectors=sectors, selected_sector=selected_sector, keyword=keyword)
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        return str(e), 500

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.json
    news_id = data.get("news_id")
    title = data.get("title")

    if not news_id or not title:
        return jsonify({"status": "error", "message": "invalid input"}), 400

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

        return jsonify({"status": "success"})
    except Exception as e:
        print(f"[ERROR] 분석 실패: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/feedback", methods=["POST"])
def feedback():
    data = request.json
    news_id = data.get("news_id")
    feedback = data.get("feedback")

    if not news_id or not feedback:
        return jsonify({"status": "error", "message": "invalid input"}), 400

    db.feedback.insert_one({
        "news_id": ObjectId(news_id),
        "feedback": feedback,
        "timestamp": datetime.utcnow()
    })

    return jsonify({"status": "success"})

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
    app.run(debug=True, port=8000, use_reloader=False)
