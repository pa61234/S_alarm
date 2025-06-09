def classify_event(text: str) -> str:
    # 간단한 rule 기반 예시 (나중에 finBERT 등으로 교체 가능)
    text = text.lower()
    if "실적" in text or "매출" in text:
        return "실적발표"
    elif "계약" in text or "공급" in text:
        return "계약"
    elif "인수" in text or "합병" in text:
        return "M&A"
    else:
        return "기타"
