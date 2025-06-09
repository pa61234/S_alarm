# S_alarm/check_feedback.py
from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()
client = MongoClient(os.getenv("MONGO_URI"))
db = client["stock_alert"]

print("📝 최근 피드백 문서 확인:")
for f in db.feedbacks.find().limit(5):
    print(f)
