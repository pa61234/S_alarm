# S_alarm/fetch_rss.py

import feedparser
from pymongo import MongoClient
from dotenv import load_dotenv
import os
from datetime import datetime, timezone, timedelta
from langdetect import detect
from ai_server_client import analyze_news  # AI 서버 연동 함수

load_dotenv()
client = MongoClient(os.getenv("MONGO_URI"))
db = client["stock_alert"]

# ✅ 한글 뉴스 중심 RSS 피드
RSS_FEEDS = {
    # 경제/금융/증권/산업/IT/제조/바이오/유통 등 다양한 언론사와 전문지
    "조선비즈": "https://biz.chosun.com/rss.xml",
    "머니투데이": "https://news.mt.co.kr/mtview/rss.htm",
    "한국경제": "https://www.hankyung.com/feed/news",
    "서울경제": "https://www.sedaily.com/rss/Finance.xml",
    "매일경제": "https://www.mk.co.kr/rss/30000001/",
    "아시아경제": "https://www.asiae.co.kr/rss/news.xml",
    "이데일리": "https://rss.edaily.co.kr/rss/Sec_list.xml",
    "전자신문": "https://rss.etnews.com/ETnews.xml",
    "ZDNet Korea": "https://zdnet.co.kr/news/news.xml",
    "디지털타임스": "https://www.dt.co.kr/rss/news.xml",
    "연합뉴스": "https://www.yna.co.kr/news/rss",
    "KDI뉴스": "https://www.kdi.re.kr/rss/kdi_news.xml",
    "파이낸셜뉴스": "https://www.fnnews.com/rss/fn_realnews_finance.xml",
    "헤럴드경제": "https://biz.heraldcorp.com/common/rss_xml.php?ct=010000000000",
    "MTN": "https://news.mtn.co.kr/newscenter/rss/news.xml",
    "한국투자증권": "https://www.koreainvestment.com/rss/news.xml",
    "NH투자증권": "https://www.nhqv.com/rss/news.xml",
    "KB증권": "https://www.kbsec.com/rss/news.xml",
    "신한투자증권": "https://www.shinhan.com/rss/news.xml",
    "디지털데일리": "https://www.digitaldaily.co.kr/rss/news.xml",
    "테크M": "https://www.techm.kr/rss/news.xml",
    "아이뉴스24": "https://www.inews24.com/rss/news.xml",
    "바이오스펙테이터": "https://www.biospectator.com/rss/news.xml",
    "팜뉴스": "https://www.pharmnews.com/rss/allArticle.xml",
    "식품저널": "https://www.foodnews.co.kr/rss/allArticle.xml",
    "파이낸셜뉴스 산업": "https://www.fnnews.com/rss/fn_industry.xml",
    "전자신문 산업": "https://rss.etnews.com/ETnews_industry.xml",
    # ... (여기에 더 많은 피드 추가 가능)
    # 영어 피드 (AI 분석 제외)
    "Yahoo Finance": "https://finance.yahoo.com/news/rssindex",
    "Bloomberg": "https://www.bloomberg.com/feeds/sitemap_news.xml",
    "Reuters": "https://www.reutersagency.com/feed/"
}

def parse_and_store(feed_url, source_name):
    feed = feedparser.parse(feed_url)
    for entry in feed.entries:
        title = entry.title
        link = entry.link
        
        # 시간 파싱 로직 개선
        published = entry.get("published", "")
        published_dt = None
        
        # 다양한 시간 형식 처리
        time_formats = [
            "%a, %d %b %Y %H:%M:%S %z",  # RFC 822 형식 (예: "Wed, 10 Jun 2025 10:55:15 +0900")
            "%a, %d %b %Y %H:%M:%S %Z",  # RFC 822 형식 (예: "Wed, 10 Jun 2025 10:55:15 KST")
            "%Y-%m-%dT%H:%M:%S%z",       # ISO 8601 형식 (예: "2025-06-10T10:55:15+09:00")
            "%Y-%m-%d %H:%M:%S",         # 기본 형식 (예: "2025-06-10 10:55:15")
        ]
        
        for fmt in time_formats:
            try:
                published_dt = datetime.strptime(published, fmt)
                # 시간대가 없는 경우 KST로 설정
                if published_dt.tzinfo is None:
                    published_dt = published_dt.replace(tzinfo=timezone(timedelta(hours=9)))
                # 시간대가 KST가 아니면 KST로 변환
                elif published_dt.tzinfo.utcoffset(published_dt) != timedelta(hours=9):
                    published_dt = published_dt.astimezone(timezone(timedelta(hours=9)))
                break
            except ValueError:
                continue
        
        # 시간 파싱 실패 시 현재 시간 사용
        if not published_dt:
            print(f"[WARNING] 시간 파싱 실패: {published}, 현재 시간으로 대체")
            published_dt = datetime.now(timezone(timedelta(hours=9)))
        
        # 중복 확인
        if db.news.find_one({"title": title, "source": source_name}):
            continue

        # ✅ 언어 감지
        try:
            lang = detect(title)
        except:
            lang = "unknown"

        # 기본 저장 구조
        doc = {
            "title": title,
            "link": link,
            "published": published_dt,
            "source": source_name,
            "lang": lang,
        }

        if lang == "ko":
            try:
                ai_result = analyze_news(title)
                if ai_result:
                    doc.update({
                        "summary": ai_result.get("summary", ""),
                        "companies": ai_result.get("companies", []),
                        "event": ai_result.get("event", ""),
                    })
                else:
                    print(f"[⚠️ 분석 실패] {title}")
            except Exception as e:
                print(f"[AI 예외 발생] {str(e)}")
                # 기본 기업명 추출 (간단한 규칙 기반)
                companies = []
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
                
                print(f"[DEBUG] 기업명 추출 시작: {title}")
                
                # 1. 정확한 기업명 매칭
                for company_list in company_keywords.values():
                    for company in company_list:
                        if company in title:
                            print(f"[DEBUG] 정확한 기업명 발견: {company}")
                            companies.append(company)
                
                # 2. 키워드 기반 매칭
                if not companies:  # 정확한 매칭이 없을 경우에만
                    for keyword, company_list in company_keywords.items():
                        if keyword in title:
                            print(f"[DEBUG] 키워드 '{keyword}' 발견, 기업 추가: {company_list}")
                            companies.extend(company_list)
                
                # 3. 기업명이 포함된 경우 (예: "삼성의", "SK가" 등)
                if not companies:  # 정확한 매칭과 키워드 매칭이 모두 없을 경우
                    for keyword, company_list in company_keywords.items():
                        if f"{keyword}의" in title or f"{keyword}가" in title or f"{keyword}는" in title:
                            print(f"[DEBUG] 기업명 포함 발견: {keyword}, 기업 추가: {company_list}")
                            companies.extend(company_list)
                
                # 4. 기업명이 포함된 경우 (예: "삼성전자 주가", "SK하이닉스 실적" 등)
                if not companies:  # 이전 매칭이 모두 없을 경우
                    for keyword, company_list in company_keywords.items():
                        for company in company_list:
                            if f"{company} 주가" in title or f"{company} 실적" in title or f"{company} 매출" in title:
                                print(f"[DEBUG] 기업 관련 키워드 발견: {company}, 기업 추가: {company}")
                                companies.append(company)
                
                # 5. 주가/실적 관련 키워드가 있는 경우
                if not companies:  # 이전 매칭이 모두 없을 경우
                    stock_keywords = ["주가", "실적", "매출", "영업이익", "순이익", "배당", "주주", "주식", "증권", "투자", "M&A", "인수", "합병"]
                    for keyword in stock_keywords:
                        if keyword in title:
                            print(f"[DEBUG] 주가/실적 관련 키워드 발견: {keyword}")
                            # 해당 키워드가 있는 뉴스는 기업 관련 뉴스로 간주
                            companies = ["기타기업"]
                            break
                
                if companies:
                    print(f"[DEBUG] 추출된 기업: {companies}")
                    doc.update({
                        "companies": companies,
                        "event": "기타"
                    })
                else:
                    print(f"[DEBUG] 기업명을 찾을 수 없음: {title}")

        db.news.insert_one(doc)

for source, url in RSS_FEEDS.items():
    parse_and_store(url, source)

print("✅ 뉴스 수집 및 저장 완료 (중복 제외 + AI 분석 적용됨)")
