# S_alarm/app.py

from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from dotenv import load_dotenv
import os
from bson import ObjectId
from datetime import datetime, timezone, timedelta
import json

from models.ner import extract_companies
from models.event_classifier import classify_event

load_dotenv()
client = MongoClient(os.getenv("MONGO_URI"))
db = client["stock_alert"]

app = Flask(__name__)

# 산업군 매핑 로드 (앱 시작 시 1회만)
with open("sector_mapping.json", "r", encoding="utf-8") as f:
    SECTOR_MAP = json.load(f)

# 유니크한 산업군 리스트
sectors = sorted(list(set(SECTOR_MAP.values())))

@app.route("/")
def index():
    try:
        # 1. 먼저 기업 정보가 있는 뉴스를 가져옴
        news = list(db.news.find({
            "companies": {"$exists": True, "$ne": []}
        }).sort("published", -1))
        
        # 2. 기업 정보가 없는 뉴스 중에서 한국어 뉴스를 가져와서 기업 정보 추출
        if len(news) < 10:  # 기업 정보가 있는 뉴스가 10개 미만인 경우
            additional_news = list(db.news.find({
                "lang": "ko",
                "companies": {"$exists": False}  # companies 필드가 없는 경우
            }).sort("published", -1).limit(20))  # 최대 20개까지 가져옴
            
            for item in additional_news:
                # 기업명 추출
                companies = extract_companies(item['title'])
                if companies:  # 기업명이 추출된 경우에만 추가
                    item['companies'] = companies
                    item['event'] = classify_event(item['title'])
                    news.append(item)
                    
                    # DB에 업데이트
                    db.news.update_one(
                        {"_id": item['_id']},
                        {"$set": {
                            "companies": companies,
                            "event": item['event'],
                            "analyzed": True
                        }}
                    )
        
        print(f"[DEBUG] 가져온 뉴스 수: {len(news)}")
        print(f"[DEBUG] 전체 뉴스 수: {db.news.count_documents({})}")
        print(f"[DEBUG] 한국어 뉴스 수: {db.news.count_documents({'lang': 'ko'})}")
        print(f"[DEBUG] 기업 관련 뉴스 수: {db.news.count_documents({'companies': {'$exists': True, '$ne': []}})}")
        
        for n in news:
            print(f"[DEBUG] 뉴스: {n['title']} | {n.get('lang', 'unknown')} | {n.get('companies', [])}")
            
        for item in news:
            item['_id'] = str(item['_id'])  # ObjectId를 문자열로 변환
            item['published'] = item['published'].replace(tzinfo=timezone.utc).astimezone(timezone(timedelta(hours=9)))
            # URL이 없는 경우 기본값 설정
            if 'url' not in item:
                item['url'] = '#'
        return render_template("index.html", news=news)
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
    app.run(debug=True, port=8000)
