from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import numpy as np
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    def __init__(self):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model_name = "monologg/kobert"
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name, trust_remote_code=True)
        self.model = AutoModelForSequenceClassification.from_pretrained(
            self.model_name,
            num_labels=3,  # positive, negative, neutral
            trust_remote_code=True
        ).to(self.device)
        
    def analyze(self, text):
        try:
            if not text or len(text.strip()) == 0:
                logger.warning("빈 텍스트가 입력되었습니다.")
                return 'unknown'
            
            logger.info(f"감성분석 시작: {text[:100]}...")
            
            # 텍스트 토큰화
            inputs = self.tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                max_length=512,
                padding=True
            ).to(self.device)
            
            # 감성분석 수행
            with torch.no_grad():
                outputs = self.model(**inputs)
                predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
                sentiment_idx = torch.argmax(predictions).item()
                
            # 결과 매핑
            sentiment_map = {
                0: "negative",
                1: "neutral",
                2: "positive"
            }
            
            sentiment = sentiment_map.get(sentiment_idx, "unknown")
            logger.info(f"감성분석 결과: {sentiment}")
            return sentiment
            
        except Exception as e:
            logger.error(f"감성분석 실패: {str(e)}")
            return 'unknown'

# 싱글톤 인스턴스 생성
sentiment_analyzer = SentimentAnalyzer() 