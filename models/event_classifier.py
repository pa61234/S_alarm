def classify_event(text):
    """
    텍스트에서 이벤트 유형을 분류합니다.
    현재는 간단한 구현으로, 실제로는 더 정교한 분류 모델을 사용해야 합니다.
    """
    # 테스트를 위한 간단한 구현
    if "투자" in text:
        return "투자"
    elif "생산" in text:
        return "생산"
    elif "분할" in text:
        return "기업구조조정"
    else:
        return "기타" 