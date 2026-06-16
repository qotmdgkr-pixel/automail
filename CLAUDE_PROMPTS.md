# Claude Code 단계별 실행 프롬프트
# 포트폴리오 자동 브리핑 시스템 — qotmdgkr-pixel

> 각 단계를 순서대로 Claude Code에 붙여넣어 실행하세요.
> GitHub 저장소: https://github.com/qotmdgkr-pixel/automail (생성 필요)

---

## STEP 1 — 프로젝트 초기화 + 가격 수집 모듈

```
d:\finance\automail 폴더에서 포트폴리오 자동 브리핑 시스템 프로젝트를 초기화해줘.

【기존 코드 위치】
d:\finance\stock_prices.py 파일이 이미 있어.
이 파일은 pykrx와 yfinance로 미국 주식 8종 + 국내 ETF 10종의 종가를 가져오는 완성된 코드야.
이 파일을 그대로 복사해서 src/price_fetcher.py로 사용하되, 아래 변경사항을 적용해줘.

【디렉터리 구조 생성】
automail/
├── .github/workflows/        (빈 폴더)
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── price_fetcher.py
│   ├── news_fetcher.py       (빈 파일, Step 2에서 작성)
│   ├── briefing_builder.py   (빈 파일, Step 3에서 작성)
│   ├── email_sender.py       (빈 파일, Step 4에서 작성)
│   └── kakao_sender.py       (빈 파일, Step 4에서 작성)
├── tests/
│   └── test_price_fetcher.py
├── requirements.txt
└── .env.example

【config.py 작성 내용】
- US_STOCKS dict: 아마존닷컴→AMZN, 브로드컴→AVGO, 알파벳A→GOOGL, 메타플랫폼스→META, 마이크로소프트→MSFT, 엔비디아→NVDA, INVESCO NASDAQ 100→QQQ, 테슬라→TSLA
- KR_ETFS list: display/keyword/code 필드 포함
  - TIGER 미국배당다우존스 / 458730
  - TIGER 미국채 10년선물 / 305080
  - ACE KRX금 현물 / 411060
  - WON S&P500 / 195930
  - SOL 미국배당다우존스(H) / 447770
  - ACE 미국하이일드액티브(H) / 479850
  - ACE 미국달러 SOFR금리(합성) / 453850
  - TIGER 은행 고배당플러스TOP10 / 449180
  - KODEX 한국 부동산리츠인프라 / 432620
  - ACE 코리아밸류업 / 475080

【price_fetcher.py 변경사항】
- 종목 정의를 config.py에서 import하도록 변경
- fetch_us()와 fetch_kr() 반환값에 등락률(change_pct) 필드 추가
  - yfinance: (현재가 - 전일 종가) / 전일 종가 * 100
  - pykrx: get_etf_ohlcv_by_date()에서 전일 대비 등락률 계산 (전일 종가 포함 기간으로 조회)
- 함수 반환값 포맷: {"name", "ticker", "price", "change_pct", "ok", "err"(선택)}
- main() 함수에서 fetch_us()와 fetch_kr() 결과를 dict로 묶어 JSON으로 data/prices.json에 저장
  - 파일 경로: automail/data/prices.json (data 폴더 자동 생성)
- print_results()는 유지

【requirements.txt】
yfinance>=0.2.40
pykrx>=1.0.47
requests>=2.31.0
python-dotenv>=1.0.0
deep-translator>=1.11.4

【.env.example】
GMAIL_SENDER=your_gmail@gmail.com
GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx
RECIPIENT_EMAIL=qotmdgkr@gmail.com
KAKAO_REST_API_KEY=your_kakao_rest_api_key
KAKAO_REFRESH_TOKEN=your_kakao_refresh_token
NEWSAPI_KEY=your_newsapi_key

【테스트】
tests/test_price_fetcher.py 작성:
- test_fetch_us_returns_8_items(): fetch_us() 결과가 8개인지 확인
- test_fetch_us_has_required_keys(): 각 항목에 name, ticker, price, change_pct, ok 키 있는지 확인
- test_kr_config_has_10_items(): KR_ETFS 길이가 10인지 확인

작성 후 python -m pytest tests/test_price_fetcher.py -v 로 테스트 실행해줘.
그리고 python src/price_fetcher.py 로 실제 실행해서 콘솔 출력과 data/prices.json 생성 확인해줘.
```

---

## STEP 2 — 뉴스 수집 모듈

```
d:\finance\automail 폴더에서 src/news_fetcher.py를 작성해줘.

【목적】
포트폴리오 종목(미국 주식 8종 + 국내 ETF 10종)의 오늘자 뉴스를
국내 3건 + 해외 3건씩 수집하고, 영문 뉴스는 한글로 번역해서
data/news.json에 저장한다.

【수집 방법 — 우선순위 순서】

방법 1: Google News RSS (메인)
- 해외 종목: f"https://news.google.com/rss/search?q={ticker}+stock&hl=en-US&gl=US&ceid=US:en"
- 국내 종목: f"https://news.google.com/rss/search?q={etf_name}&hl=ko&gl=KR&ceid=KR:ko"
- feedparser 라이브러리로 파싱 (requirements.txt에 feedparser>=6.0.10 추가)
- 오늘 날짜(KST) 기준 발행된 항목만 필터링
- 중복 URL 제거

방법 2: NewsAPI (폴백 — NEWSAPI_KEY 환경변수 있을 때만)
- endpoint: https://newsapi.org/v2/everything
- 파라미터: q=ticker, from=오늘날짜, sortBy=publishedAt, language=en, pageSize=5
- 환경변수 NEWSAPI_KEY가 없으면 이 방법 건너뜀

【번역】
- deep_translator 라이브러리의 GoogleTranslator 사용
- 영문 뉴스 제목(title)과 요약(summary) 번역
- 번역 실패 시 원문 그대로 사용 (예외 처리)
- from deep_translator import GoogleTranslator
- translator = GoogleTranslator(source='en', target='ko')

【출력 구조 — data/news.json】
{
  "fetched_at": "2026-06-15T06:30:00",
  "date": "2026-06-15",
  "items": {
    "AMZN": {
      "name": "아마존닷컴",
      "domestic": [
        {"title": "제목", "url": "https://...", "source": "출처", "published": "2026-06-15"}
      ],
      "international": [
        {"title": "번역된 제목", "title_original": "Original title",
         "url": "https://...", "source": "출처", "published": "2026-06-15"}
      ]
    },
    "458730": { ... }  // 국내 ETF는 종목코드를 키로 사용
  }
}

【국내/해외 뉴스 분류 기준】
- 국내 ETF(KR_ETFS): 국내 뉴스 → 한글 키워드 RSS 검색, 해외 뉴스 → 영문 ETF 이름 검색
- 미국 주식(US_STOCKS): 국내 뉴스 → "아마존 주가" 형태 한글 검색, 해외 뉴스 → 티커 영문 검색

【함수 구성】
- fetch_news_for_ticker(ticker, name_kr, name_en) → {"domestic": [...], "international": [...]}
- translate_text(text) → str (번역된 텍스트, 실패 시 원문)
- fetch_all_news(us_stocks, kr_etfs) → news_data dict
- save_news(news_data) → data/news.json 저장
- main() → fetch_all_news() 실행 후 저장, 콘솔에 종목별 수집 건수 출력

【오류 처리】
- 뉴스가 0건이어도 에러 없이 빈 리스트로 처리
- 네트워크 오류 시 해당 종목만 스킵하고 계속 진행
- 최대 재시도 2회 (requests timeout=10)

requirements.txt에 feedparser>=6.0.10 추가해줘.

작성 후 python src/news_fetcher.py 실행해서 콘솔 출력과 data/news.json 생성을 확인해줘.
```

---

## STEP 3 — 브리핑 생성 모듈

```
d:\finance\automail 폴더에서 src/briefing_builder.py를 작성해줘.

【목적】
data/prices.json과 data/news.json을 읽어서
- 이메일용 HTML 브리핑
- 카카오톡용 텍스트 브리핑
두 가지 포맷으로 생성하고 data/briefing_email.html과 data/briefing_kakao.txt로 저장한다.

【이메일용 HTML 포맷】
- 전체를 인라인 CSS로 스타일링 (Gmail 호환)
- 상단 헤더: "📊 포트폴리오 브리핑 | YYYY-MM-DD"
- 섹션 1: 미국 주식 종가 테이블
  - 컬럼: 종목명 | 티커 | 현재가(USD) | 등락률
  - 등락률 양수 → 초록(#16a34a), 음수 → 빨강(#dc2626), 텍스트 색상
  - 등락 화살표: ▲ (양수) / ▼ (음수)
- 섹션 2: 국내 ETF 종가 테이블
  - 컬럼: 종목명 | 코드 | 현재가(KRW) | 등락률
  - 동일한 색상 규칙 적용
- 섹션 3: 오늘의 뉴스 (종목별)
  - 미국 주식 → 국내 뉴스 3건, 해외 뉴스 3건 (번역 제목 + 원문 제목 병기)
  - 국내 ETF → 국내 뉴스 3건, 해외 뉴스 3건
  - 뉴스 없는 종목: "오늘 관련 뉴스 없음" 표시
  - 뉴스 제목은 URL 하이퍼링크로 연결
- 하단 푸터: "기준일: YYYY-MM-DD | 자동 생성"

【카카오톡용 텍스트 포맷】
카카오 메시지 텍스트 타입 최대 2000자 제한 엄수.
초과 시 뉴스 건수를 줄이고 (국내 2건, 해외 2건 → 1건), 그래도 초과 시 뉴스 섹션 생략.

형식:
```
📊 포트폴리오 브리핑 | 2026-06-15
━━━━━━━━━━━━━━━━━━━━

📈 미국 주식 (USD)
아마존닷컴(AMZN)  $195.32  ▲+1.23%
브로드컴(AVGO)    $185.40  ▼-0.45%
...

🇰🇷 국내 ETF (KRW)
TIGER 미국배당다우존스  12,345원  ▲+0.54%
...

📰 주요 뉴스
▶ 아마존닷컴
 [국] ① 제목 (출처)
 [해] ① 번역된 제목 (출처)

━━━━━━━━━━━━━━━━━━━━
자동생성 | 2026-06-15
```

【함수 구성】
- load_data() → (prices_data, news_data) tuple 로드
- build_email_html(prices, news) → str (HTML 전체)
- build_kakao_text(prices, news) → str (텍스트, 2000자 이하 보장)
- save_briefings(html, text) → 파일 저장
- main() → 전체 실행

작성 후 python src/briefing_builder.py 실행해서
data/briefing_email.html을 브라우저로 열어 레이아웃 확인하고,
data/briefing_kakao.txt 내용을 콘솔에 출력해줘.
글자수도 함께 출력해줘.
```

---

## STEP 4 — 이메일 + 카카오톡 발송 모듈

```
d:\finance\automail 폴더에서 src/email_sender.py와 src/kakao_sender.py를 작성해줘.

【email_sender.py — Gmail SMTP 발송】

조건:
- smtplib + email.mime 사용 (외부 라이브러리 최소화)
- Gmail SMTP: smtp.gmail.com, port 587, STARTTLS
- 환경변수: GMAIL_SENDER, GMAIL_APP_PASSWORD, RECIPIENT_EMAIL
- data/briefing_email.html 파일을 읽어 HTML 이메일로 발송
- 제목: "[포트폴리오 브리핑] YYYY-MM-DD 종가 및 주요 뉴스"
- Content-Type: multipart/alternative (text + HTML)
- text 파트: data/briefing_kakao.txt 내용 (HTML 미지원 클라이언트 대비)

함수:
- load_env(): python-dotenv로 .env 로드 (파일 있을 때만, 없으면 OS 환경변수 사용)
- send_email(subject, html_body, text_body) → bool
- main(): briefing 파일 읽기 → send_email() 호출 → 성공/실패 출력

오류 처리:
- 환경변수 누락 시 명확한 에러 메시지 출력 후 종료 (sys.exit(1))
- SMTP 연결 실패 시 에러 메시지 출력 (재시도 없음)

【kakao_sender.py — 카카오 나에게 보내기】

카카오 REST API 나에게 보내기 절차:
1. refresh_token으로 access_token 재발급
   POST https://kauth.kakao.com/oauth/token
   body: grant_type=refresh_token&client_id={REST_API_KEY}&refresh_token={REFRESH_TOKEN}
   → 응답에서 access_token 추출

2. 텍스트 메시지 발송
   POST https://kapi.kakao.com/v2/api/talk/memo/default/send
   Header: Authorization: Bearer {access_token}
   body: template_object={"object_type":"text","text":"...","link":{"web_url":"","mobile_web_url":""}}

환경변수: KAKAO_REST_API_KEY, KAKAO_REFRESH_TOKEN

함수:
- get_access_token(rest_api_key, refresh_token) → str (access_token)
- send_kakao_message(access_token, text) → bool
- main():
  - data/briefing_kakao.txt 읽기
  - 텍스트 2000자 초과 시 자동으로 1900자로 자르고 "...(생략)" 추가
  - get_access_token() → send_kakao_message() → 성공/실패 출력

오류 처리:
- 환경변수 누락 시 에러 메시지 출력 후 sys.exit(1)
- token 재발급 실패 시 에러 상세 출력 후 sys.exit(1)
- 메시지 발송 실패 시 응답 코드와 본문 출력

【통합 실행 스크립트 — src/main.py 작성】
price_fetcher, news_fetcher, briefing_builder, email_sender, kakao_sender를 순서대로 실행하는
통합 스크립트. 각 단계 성공/실패를 콘솔에 출력.

실행 순서:
1. price_fetcher.main()
2. news_fetcher.main()
3. briefing_builder.main()
4. email_sender.main()
5. kakao_sender.main()

각 단계 실패 시 이후 단계 스킵하지 않고 계속 진행 (독립적 실행).
최종 결과 요약 출력.

【로컬 테스트 방법】
.env 파일 생성 후 (GMAIL_APP_PASSWORD와 KAKAO_REFRESH_TOKEN 실제 값 입력)
python src/email_sender.py 실행해서 메일 수신 확인
python src/kakao_sender.py 실행해서 카카오톡 수신 확인
```

---

## STEP 5 — GitHub Actions + 배포 설정

```
d:\finance\automail 폴더에서 GitHub Actions 워크플로우를 작성하고 배포 준비를 완료해줘.

【워크플로우 파일 1】 .github/workflows/email_briefing.yml

name: Daily Email Briefing
트리거:
- schedule: cron '35 21 * * *'  (매일 KST 06:35 = UTC 21:35 전날)
- workflow_dispatch: (수동 실행 + cron-job.org 웹훅용)

jobs.send-email:
- runs-on: ubuntu-latest
- steps:
  1. actions/checkout@v4
  2. actions/setup-python@v5 (python-version: '3.11')
  3. pip install -r requirements.txt
  4. python src/main.py --mode email
     (email 모드: price_fetcher + news_fetcher + briefing_builder + email_sender만 실행)
- env (GitHub Secrets에서):
  GMAIL_SENDER, GMAIL_APP_PASSWORD, RECIPIENT_EMAIL, NEWSAPI_KEY

【워크플로우 파일 2】 .github/workflows/kakao_briefing.yml

name: Daily KakaoTalk Briefing
트리거:
- schedule: cron '39 21 * * *'  (매일 KST 06:39 = UTC 21:39 전날)
- workflow_dispatch:

jobs.send-kakao:
- runs-on: ubuntu-latest
- steps:
  1. actions/checkout@v4
  2. actions/setup-python@v5 (python-version: '3.11')
  3. pip install -r requirements.txt
  4. python src/main.py --mode kakao
     (kakao 모드: price_fetcher + news_fetcher + briefing_builder + kakao_sender만 실행)
- env:
  KAKAO_REST_API_KEY, KAKAO_REFRESH_TOKEN, NEWSAPI_KEY

【main.py 수정】
--mode 인수 추가 (argparse):
- --mode email: 이메일만 발송
- --mode kakao: 카카오톡만 발송
- --mode all (기본값): 모두 발송

【.gitignore 작성】
.env
data/
__pycache__/
*.pyc
.pytest_cache/
*.egg-info/

【README.md 작성 (간략)】
- 프로젝트 설명 (1~2줄)
- 필요한 GitHub Secrets 목록과 설명
- cron-job.org 설정 방법
  1. cron-job.org 가입 → New Cronjob 생성
  2. URL: https://api.github.com/repos/qotmdgkr-pixel/automail/actions/workflows/email_briefing.yml/dispatches
  3. Method: POST
  4. Headers: Authorization: Bearer {GITHUB_PAT}, Accept: application/vnd.github+json, Content-Type: application/json
  5. Body: {"ref":"main"}
  6. Schedule: 35 21 * * * (이메일), 39 21 * * * (카카오)
  - GitHub PAT 발급 방법: Settings → Developer settings → Personal access tokens → workflow 권한

- 로컬 실행 방법:
  pip install -r requirements.txt
  cp .env.example .env  # .env에 실제 값 입력
  python src/main.py

【Git 초기화 및 GitHub 연동 명령어 안내】
아래 명령어들을 순서대로 안내해줘 (실행은 하지 말고 출력만):

cd d:\finance\automail
git init
git add .
git commit -m "feat: 포트폴리오 자동 브리핑 시스템 초기 구현"
git branch -M main
git remote add origin https://github.com/qotmdgkr-pixel/automail.git
git push -u origin main

GitHub Secrets 등록 안내:
Settings → Secrets and variables → Actions → New repository secret
- GMAIL_SENDER
- GMAIL_APP_PASSWORD
- RECIPIENT_EMAIL
- KAKAO_REST_API_KEY
- KAKAO_REFRESH_TOKEN
- NEWSAPI_KEY (선택)

모든 파일 작성 완료 후 최종 디렉터리 구조를 tree 명령으로 출력해줘.
```

---

## 참고: 단계별 검증 체크리스트

| 단계 | 확인 항목 |
|------|-----------|
| Step 1 | `data/prices.json` 생성 확인, 등락률 포함 여부 |
| Step 2 | `data/news.json` 생성 확인, 번역 적용 여부 |
| Step 3 | HTML 브리핑 브라우저 렌더링, 카카오 텍스트 2000자 이하 |
| Step 4 | 이메일 수신 확인, 카카오톡 메시지 수신 확인 |
| Step 5 | GitHub Push 완료, Actions 탭에서 workflow 확인, cron-job.org 등록 |
