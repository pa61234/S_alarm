# S_alarm/ai_server_client.py

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time

def analyze_news(text: str, max_retries=3, retry_delay=1):
    # 재시도 전략 설정
    retry_strategy = Retry(
        total=max_retries,
        backoff_factor=0.5,
        status_forcelist=[500, 502, 503, 504]
    )
    
    # 세션 생성 및 재시도 전략 적용
    session = requests.Session()
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    
    try:
        response = session.post(
            "http://127.0.0.1:5001/analyze",
            json={"text": text},
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        else:
            print(f"[AI 서버 오류] 상태코드: {response.status_code}")
            return None
    except requests.exceptions.ConnectionError as e:
        print(f"[AI 서버 연결 실패] {str(e)}")
        # 연결 실패 시 잠시 대기 후 재시도
        time.sleep(retry_delay)
        return None
    except Exception as e:
        print(f"[AI 예외 발생] {str(e)}")
        return None
