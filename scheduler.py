# scheduler.py
import schedule
import time
import subprocess

def job():
    print("🔄 fetch_rss.py 실행 중...")
    subprocess.run(["python", "fetch_rss.py"])
    print("✅ 실행 완료")

# 10분마다 실행 (원하면 수정 가능)
schedule.every(10).minutes.do(job)

print("⏱ 예약 실행 시작됨 (10분마다 fetch_rss.py 실행)")

while True:
    schedule.run_pending()
    time.sleep(1)
