def extract_companies(text):
    """
    텍스트에서 회사명을 추출합니다.
    """
    companies = []
    
    # 기업명 키워드 매핑
    company_keywords = {
        "삼성": ["삼성전자", "삼성SDI", "삼성생명", "삼성화재", "삼성카드"],
        "SK": ["SK하이닉스", "SK이노베이션", "SK텔레콤", "SK바이오사이언스"],
        "LG": ["LG전자", "LG디스플레이", "LG화학", "LG에너지솔루션"],
        "현대": ["현대자동차", "현대모비스", "현대제철", "현대글로비스"],
        "네이버": ["네이버"],
        "카카오": ["카카오"],
        "KT": ["KT"],
        "롯데": ["롯데정보통신", "롯데케미칼", "롯데지주"],
        "포스코": ["포스코", "포스코퓨처엠"],
        "CJ": ["CJ제일제당", "CJ대한통운", "CJ CGV"],
        "GS": ["GS건설", "GS리테일", "GS칼텍스"],
        "한화": ["한화시스템", "한화솔루션", "한화생명"],
        "두산": ["두산중공업", "두산퓨얼셀"],
        "LS": ["LS전선", "LS일렉트릭"],
        "효성": ["효성첨단소재", "효성티앤씨"],
        "아모레": ["아모레퍼시픽"],
        "신세계": ["신세계", "신세계인터내셔날"],
        "이마트": ["이마트"],
        "하이닉스": ["SK하이닉스"],
        "엔씨소프트": ["엔씨소프트"],
        "넥슨": ["넥슨"],
        "크래프톤": ["크래프톤"],
        "스마일게이트": ["스마일게이트"],
        "카카오게임즈": ["카카오게임즈"],
        "펄어비스": ["펄어비스"],
        "넷마블": ["넷마블"],
        "컴투스": ["컴투스"],
        "위메이드": ["위메이드"],
        "그라비티": ["그라비티"],
        "액토즈소프트": ["액토즈소프트"],
        "데브시스터즈": ["데브시스터즈"]
    }
    
    # 1. 정확한 기업명 매칭
    for company_list in company_keywords.values():
        for company in company_list:
            if company in text:
                companies.append(company)
    
    # 2. 키워드 기반 매칭
    if not companies:  # 정확한 매칭이 없을 경우에만
        for keyword, company_list in company_keywords.items():
            if keyword in text:
                companies.extend(company_list)
    
    # 3. 기업명이 포함된 경우 (예: "삼성의", "SK가" 등)
    if not companies:  # 정확한 매칭과 키워드 매칭이 모두 없을 경우
        for keyword, company_list in company_keywords.items():
            if f"{keyword}의" in text or f"{keyword}가" in text or f"{keyword}는" in text:
                companies.extend(company_list)
    
    # 4. 기업명이 포함된 경우 (예: "삼성전자 주가", "SK하이닉스 실적" 등)
    if not companies:  # 이전 매칭이 모두 없을 경우
        for keyword, company_list in company_keywords.items():
            for company in company_list:
                if f"{company} 주가" in text or f"{company} 실적" in text or f"{company} 매출" in text:
                    companies.append(company)
    
    return list(set(companies))  # 중복 제거 