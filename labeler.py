import re

def label_event(title: str) -> str:
    title = title.lower()

    guidance_keywords = ["guidance", "forecast", "outlook", "estimate"]
    merger_keywords = ["acquire", "merger", "buyout", "takeover", "deal"]
    earnings_keywords = ["earnings", "profit", "loss", "q1", "q2", "q3", "q4", "eps", "results"]
    labor_keywords = ["strike", "union", "contract", "ratify", "labor"]

    if any(k in title for k in guidance_keywords):
        return "GUIDANCE"
    elif any(k in title for k in merger_keywords):
        return "MERGER"
    elif any(k in title for k in earnings_keywords):
        return "EARNINGS"
    elif any(k in title for k in labor_keywords):
        return "LABOR"
    else:
        return "OTHER"

def extract_company(title: str) -> str:
    # 괄호 안에 있는 티커 추출 예: "Nvidia Corporation (NVDA)"
    match = re.search(r"\(([^)]+)\)", title)
    if match:
        return match.group(1).upper()  # 티커 반환
    return title.split()[0].capitalize()  # 티커 없으면 앞 단어
