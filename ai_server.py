from flask import Flask, request, jsonify
from models.ner import extract_companies
from models.event_classifier import classify_event

app = Flask(__name__)

@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        data = request.json
        text = data.get("text", "")
        
        if not text:
            return jsonify({"error": "텍스트가 없습니다."}), 400
            
        # 기업명 추출
        companies = extract_companies(text)
        
        # 이벤트 분류
        event = classify_event(text)
        
        return jsonify({
            "companies": companies,
            "event": event
        })
    except Exception as e:
        print(f"[AI 서버 오류] {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001, debug=True) 