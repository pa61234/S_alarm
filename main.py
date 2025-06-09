# S_alarm/main.py

from flask import Flask, render_template, request
from pymongo import MongoClient
from bson import ObjectId
from dotenv import load_dotenv
import os
from datetime import datetime

# 환경 변수 로드
load_dotenv()

# Flask 앱 생성
app = Flask(__name__)

# MongoDB 연결
client = MongoClient(os.getenv("MONGO_URI"), tls=True, tlsAllowInvalidCertificates=True)
db = client["stock_alert"]

@app.route("/")
def index():
    news_items = list(db.news.find().sort("published", -1).limit(50))
    return render_template("index.html", news_list=news_items)

@app.route("/feedback", methods=["POST"])
def feedback():
    data = request.get_json()
    news_id = data.get("news_id")
    feedback_value = data.get("feedback")
    timestamp = datetime.now()

    try:
        news_object_id = ObjectId(news_id)
    except Exception:
        news_object_id = None

    db.feedbacks.insert_one({
        "news_id": news_object_id,
        "feedback": feedback_value,
        "timestamp": timestamp
    })

    return {"status": "success"}

@app.route("/feedbacks")
def view_feedbacks():
    feedbacks_raw = list(db.feedbacks.find().sort("timestamp", -1).limit(20))
    feedback_list = []

    for fb in feedbacks_raw:
        news = None
        news_id = fb.get("news_id")
        if news_id:
            news = db.news.find_one({"_id": news_id})
        feedback_list.append({
            "title": news["title"] if news else "(제목 없음)",
            "feedback": fb.get("feedback", "(알 수 없음)"),
            "timestamp": fb.get("timestamp")
        })

    return render_template("feedbacks.html", feedbacks=feedback_list)

if __name__ == "__main__":
    app.run(debug=True)
