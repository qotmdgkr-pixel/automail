"""포트폴리오 종목 정의"""

US_STOCKS = {
    "아마존닷컴":         "AMZN",
    "브로드컴":           "AVGO",
    "알파벳 A":           "GOOGL",
    "메타플랫폼스":       "META",
    "마이크로소프트":     "MSFT",
    "엔비디아":           "NVDA",
    "INVESCO NASDAQ 100": "QQQ",
    "테슬라":             "TSLA",
}

# display: 화면 출력용 이름
# keyword: pykrx 이름 검색용 (공백·괄호 제거)
# code:    KRX 종목코드 (우선 사용, 검색 폴백용)
KR_ETFS = [
    {"display": "TIGER 미국배당다우존스",      "keyword": "TIGER미국배당다우존스",   "code": "458730"},
    {"display": "TIGER 미국채 10년선물",        "keyword": "TIGER미국채10년선물",     "code": "305080"},
    {"display": "ACE KRX금 현물",              "keyword": "ACEKRX금현물",            "code": "411060"},
    {"display": "WON S&P500",                  "keyword": "WONS&P500",               "code": "195930"},
    {"display": "SOL 미국배당다우존스(H)",      "keyword": "SOL미국배당다우존스",     "code": "447770"},
    {"display": "ACE 미국하이일드액티브(H)",    "keyword": "ACE미국하이일드액티브",   "code": "479850"},
    {"display": "ACE 미국달러 SOFR금리(합성)", "keyword": "ACE미국달러SOFR금리",     "code": "453850"},
    {"display": "TIGER 은행 고배당플러스TOP10","keyword": "TIGER은행고배당플러스",   "code": "449180"},
    {"display": "KODEX 한국 부동산리츠인프라", "keyword": "KODEX한국부동산리츠",     "code": "476800"},
    {"display": "ACE 코리아밸류업",            "keyword": "ACE코리아밸류업",         "code": "475080"},
]
