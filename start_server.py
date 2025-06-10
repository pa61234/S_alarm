import subprocess
import sys
import os

def start_server():
    try:
        # 서버가 이미 실행 중인지 확인
        result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True)
        if '8000' in result.stdout:
            print("서버가 이미 실행 중입니다.")
            return
        
        # 서버 시작
        print("서버를 시작합니다...")
        subprocess.Popen([sys.executable, 'app.py'], 
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL)
        print("서버가 시작되었습니다.")
        
    except Exception as e:
        print(f"서버 시작 중 오류 발생: {str(e)}")

if __name__ == "__main__":
    start_server() 