def extract_companies(text):
    """
    텍스트에서 회사명을 추출합니다.
    """
    companies = []
    
    # 기업명 키워드 매핑
    company_keywords = {
        # IT/인터넷
        "삼성전자": ["삼성전자", "삼성"],
        "SK하이닉스": ["SK하이닉스", "하이닉스"],
        "네이버": ["네이버", "NAVER"],
        "카카오": ["카카오", "Kakao"],
        "엔씨소프트": ["엔씨소프트", "NC소프트", "NC"],
        "넥슨": ["넥슨", "Nexon"],
        "LG전자": ["LG전자", "LG"],
        "KT": ["KT", "케이티"],
        "SK텔레콤": ["SK텔레콤", "SKT"],
        "LG유플러스": ["LG유플러스", "LGU+", "엘지유플러스"],
        # 자동차/부품
        "현대자동차": ["현대자동차", "현대차", "현대"],
        "기아": ["기아", "기아차"],
        "현대모비스": ["현대모비스"],
        "현대글로비스": ["현대글로비스"],
        "만도": ["만도"],
        # 바이오/제약
        "셀트리온": ["셀트리온"],
        "삼성바이오로직스": ["삼성바이오로직스", "삼성바이오"],
        "한미약품": ["한미약품"],
        "유한양행": ["유한양행"],
        "종근당": ["종근당"],
        # 유통/식품
        "신세계": ["신세계"],
        "이마트": ["이마트"],
        "롯데쇼핑": ["롯데쇼핑"],
        "CJ제일제당": ["CJ제일제당", "CJ"],
        "오뚜기": ["오뚜기"],
        "농심": ["농심"],
        # 건설/중공업
        "현대건설": ["현대건설"],
        "삼성물산": ["삼성물산"],
        "GS건설": ["GS건설"],
        "대우건설": ["대우건설"],
        "두산중공업": ["두산중공업", "두산에너빌리티"],
        # 금융/증권
        "삼성생명": ["삼성생명"],
        "삼성화재": ["삼성화재"],
        "신한은행": ["신한은행", "신한"],
        "KB국민은행": ["KB국민은행", "국민은행", "KB"],
        "NH농협": ["NH농협", "농협"],
        "카카오뱅크": ["카카오뱅크"],
        # 기타 대기업/그룹
        "포스코": ["포스코", "POSCO"],
        "한화": ["한화"],
        "LS": ["LS", "LS전선", "LS일렉트릭"],
        "효성": ["효성", "효성첨단소재", "효성티앤씨"],
        "아모레퍼시픽": ["아모레퍼시픽", "아모레"],
        "한진칼": ["한진칼", "한진"],
        "대한항공": ["대한항공"],
        "HMM": ["HMM", "현대상선"],
        # 코스닥 대표
        "펄어비스": ["펄어비스"],
        "카카오게임즈": ["카카오게임즈"],
        "컴투스": ["컴투스"],
        "위메이드": ["위메이드"],
        "넷마블": ["넷마블"],
        "크래프톤": ["크래프톤"],
        "스마일게이트": ["스마일게이트"],
        "그라비티": ["그라비티"],
        "액토즈소프트": ["액토즈소프트"],
        "데브시스터즈": ["데브시스터즈"],
        # 기타 주요 상장사 및 브랜드, 약어, 그룹명 등 추가
        # ... (여기에 더 많은 상장사/브랜드/약어/그룹명 추가 가능)
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