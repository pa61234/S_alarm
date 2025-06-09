import requests
import json

# API 엔드포인트
url = "http://localhost:5001/analyze"

# 테스트 데이터
data = {
    "news_id": "68465e8f1d09dc79210767a1",
    "title": "삼성전자, AI 반도체 시장 공략 강화...신규 투자 발표"
}

# POST 요청 보내기
response = requests.post(url, json=data)

# 응답 출력
print("Status Code:", response.status_code)
print("Response:", response.json()) 