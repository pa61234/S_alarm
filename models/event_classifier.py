def classify_event(text):
    """
    뉴스 제목에서 이벤트 유형을 분류합니다.
    """
    # 실적 관련
    if any(keyword in text for keyword in ["실적", "매출", "영업이익", "순이익", "손익", "흑자", "적자", "수익", "매출액"]):
        return "실적"
    
    # 주가/투자 관련
    if any(keyword in text for keyword in ["주가", "주식", "투자", "매수", "매도", "매매", "거래량", "시가총액", "시총"]):
        return "주가/투자"
    
    # 신규 사업/제품
    if any(keyword in text for keyword in ["출시", "신규", "신제품", "신사업", "진출", "도입", "개발", "출시", "선보"]):
        return "신규사업"
    
    # M&A/인수
    if any(keyword in text for keyword in ["인수", "합병", "M&A", "매각", "투자", "지분", "인수합병", "매입"]):
        return "M&A/인수"
    
    # 리스크/사고
    if any(keyword in text for keyword in ["사고", "화재", "폭발", "사망", "부상", "피해", "손실", "리스크", "위기", "문제"]):
        return "리스크"
    
    # 정책/규제
    if any(keyword in text for keyword in ["정책", "규제", "법안", "법률", "제도", "허가", "승인", "인가", "규정"]):
        return "정책/규제"
    
    # 기술/특허
    if any(keyword in text for keyword in ["기술", "특허", "연구", "개발", "R&D", "발명", "혁신", "기술력"]):
        return "기술/특허"
    
    # 채용/인사
    if any(keyword in text for keyword in ["채용", "인사", "임원", "사장", "CEO", "부사장", "이사", "퇴임", "사임"]):
        return "채용/인사"
    
    # 파트너십/협력
    if any(keyword in text for keyword in ["협력", "제휴", "파트너십", "계약", "MOU", "협약", "동맹", "협업"]):
        return "파트너십"
    
    # 시설/공장
    if any(keyword in text for keyword in ["공장", "시설", "증설", "확장", "이전", "건설", "착공", "준공"]):
        return "시설/공장"
    
    # 배당/주주환원
    if any(keyword in text for keyword in ["배당", "주주환원", "자사주", "소각", "환매", "주주"]):
        return "배당/환원"
    
    # ESG/환경
    if any(keyword in text for keyword in ["ESG", "환경", "친환경", "탄소", "기후", "사회공헌", "지속가능"]):
        return "ESG/환경"
    
    # 해외진출
    if any(keyword in text for keyword in ["해외", "글로벌", "수출", "진출", "현지화", "해외법인", "해외지사"]):
        return "해외진출"
    
    # 기타
    return "기타" 