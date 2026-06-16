# PRD: 포트폴리오 자동 브리핑 시스템

## 1. 개요

### 1.1 프로젝트 목적
매일 아침 포트폴리오 종목의 전일 종가와 관련 뉴스를 자동으로 수집·번역·정리하여, 이메일과 카카오톡으로 브리핑을 발송하는 시스템을 구축한다.

### 1.2 발송 채널 및 일정
| 채널 | 시간 | 수신처 |
|------|------|--------|
| 이메일 | 매일 06:35 KST | qotmdgkr@gmail.com |
| 카카오톡 | 매일 06:39 KST | 본인 계정 |

### 1.3 실행 인프라
- 소스코드: GitHub 저장소 관리
- 스케줄러: [cron-job.org](https://console.cron-job.org/) → GitHub Actions Webhook 트리거
- 런타임: GitHub Actions (ubuntu-latest)

---

## 2. 포트폴리오 종목

### 2.1 해외 주식 (yfinance로 가격 수집)
| 종목명 | 티커 |
|--------|------|
| Amazon.com | AMZN |
| Broadcom | AVGO |
| Alphabet A | GOOGL |
| Meta Platforms | META |
| Microsoft | MSFT |
| Nvidia | NVDA |
| Invesco NASDAQ 100 ETF | QQQ |
| Tesla | TSLA |

### 2.2 국내 ETF (pykrx로 가격 수집)
| 종목명 | 종목코드 |
|--------|---------|
| TIGER 미국배당다우존스 | 458730 |
| TIGER 미국채 10년선물 | 305080 |
| ACE KRX금 현물 | 411060 |
| WON S&P500 | 195930 |
| SOL 미국배당다우존스(H) | 447770 |
| ACE 미국하이일드액티브(H) | 479850 |
| ACE 미국달러 SOFR금리(합성) | 453850 |
| TIGER 은행 고배당플러스TOP10 | 449180 |
| KODEX 한국 부동산리츠인프라 | 432620 |
| ACE 코리아밸류업 | 475080 |

---

## 3. 기능 요구사항

### 3.1 가격 수집 모듈 (`price_fetcher.py`)

#### 3.1.1 해외 주식 (yfinance)
- `yfinance` 라이브러리를 사용하여 전일 종가(Close), 등락률(%), 52주 고/저가 수집
- 미국 장 마감(현지 기준 전날) 기준 종가 사용
- 환율(USD/KRW) 함께 표시 (선택)

#### 3.1.2 국내 ETF (pykrx)
- `pykrx` 라이브러리를 사용하여 전일 종가, 등락률, 거래량 수집
- KRX 기준 전일 종가 사용 (장 마감 이후 기준)
- 공휴일·휴장일 처리: 직전 거래일 기준으로 자동 fallback

#### 3.1.3 출력 포맷 예시
```
[해외주식]
AMZN (Amazon)   $195.32  ▲ +1.23%
NVDA (Nvidia)   $131.50  ▼ -0.87%

[국내 ETF]
TIGER 미국배당다우존스  12,345원  ▲ +0.54%
ACE KRX금 현물        14,210원  ▼ -0.21%
```

---

### 3.2 뉴스 수집 모듈 (`news_fetcher.py`)

#### 3.2.1 수집 방법 (우선순위)
1. **RSS 피드**: Yahoo Finance RSS, Google News RSS (종목명/티커 기반)
2. **NewsAPI**: newsapi.org 무료 플랜 (하루 100건 제한 내)
3. **WebSearch 폴백**: 위 두 방법 실패 시 DuckDuckGo 등 검색 API

#### 3.2.2 수집 기준
- **오늘 날짜** 발행 뉴스 (UTC 기준 당일 00:00 이후)
- **국내 뉴스**: 네이버 금융 RSS, 한국경제, 매일경제 RSS 활용 → 종목당 최대 3건
- **해외 뉴스**: Yahoo Finance RSS, Google News (영문) → 종목당 최대 3건
- 중복 URL 필터링 적용

#### 3.2.3 번역
- 해외(영문) 뉴스 제목 및 요약은 **한국어로 번역** 후 브리핑에 포함
- 번역 방법: `deep-translator` 라이브러리 (Google Translate API 무료 버전) 또는 Claude API

---

### 3.3 브리핑 생성 모듈 (`briefing_builder.py`)

#### 3.3.1 구성
```
==============================
📊 포트폴리오 브리핑 | 2026-06-15
==============================

[📈 해외주식 종가]
...종목별 가격 테이블...

[🇰🇷 국내 ETF 종가]
...종목별 가격 테이블...

[📰 오늘의 주요 뉴스]

▶ Amazon (AMZN)
  [국내] 1. 제목 - 출처
         2. 제목 - 출처
         3. 제목 - 출처
  [해외] 1. (번역된)제목 - 출처
         2. (번역된)제목 - 출처
         3. (번역된)제목 - 출처

▶ Nvidia (NVDA)
  ...

[전체 뉴스 없는 종목은 "오늘 관련 뉴스 없음"으로 표시]

==============================
📅 기준일: YYYY-MM-DD  |  자동생성
==============================
```

#### 3.3.2 두 가지 포맷 생성
- **이메일용**: HTML 포맷 (표, 색상 강조)
- **카카오톡용**: 텍스트 포맷 (이모지 활용, 2000자 이내)

---

### 3.4 이메일 발송 모듈 (`email_sender.py`)
- Gmail API (OAuth2) 또는 SMTP(`smtplib`) + Gmail 앱 비밀번호
- 수신자: qotmdgkr@gmail.com
- 제목: `[포트폴리오 브리핑] YYYY-MM-DD 종가 및 주요 뉴스`
- 본문: HTML 형식
- 발송 시각: 매일 **06:35 KST** (GitHub Actions cron = `21 35 * * *` UTC+0, 즉 KST 6:35 = UTC 21:35 전날)

---

### 3.5 카카오톡 발송 모듈 (`kakao_sender.py`)
- 카카오 REST API (나에게 보내기) 사용
  - 토큰 갱신: `refresh_token`을 GitHub Secrets에 저장, 실행 시마다 `access_token` 재발급
  - API 엔드포인트: `https://kapi.kakao.com/v2/api/talk/memo/default/send`
- 메시지 타입: `text` 또는 `feed` 타입
- 발송 시각: 매일 **06:39 KST** (UTC 21:39 전날 기준)

---

## 4. 디렉터리 구조

```
automail/
├── .github/
│   └── workflows/
│       ├── email_briefing.yml     # 매일 21:35 UTC → 이메일 발송
│       └── kakao_briefing.yml     # 매일 21:39 UTC → 카카오톡 발송
├── src/
│   ├── price_fetcher.py           # 가격 수집 (pykrx + yfinance)
│   ├── news_fetcher.py            # 뉴스 수집 + 번역
│   ├── briefing_builder.py        # 브리핑 조합
│   ├── email_sender.py            # Gmail 발송
│   ├── kakao_sender.py            # 카카오톡 발송
│   └── config.py                  # 종목 목록, 설정값
├── tests/
│   ├── test_price_fetcher.py
│   └── test_news_fetcher.py
├── requirements.txt
├── .env.example                   # 환경변수 예시 (실제 값은 GitHub Secrets)
└── PRD.md
```

---

## 5. 환경변수 / GitHub Secrets

| 키 이름 | 설명 |
|--------|------|
| `GMAIL_SENDER` | 발신 Gmail 주소 |
| `GMAIL_APP_PASSWORD` | Gmail 앱 비밀번호 (2FA 설정 필요) |
| `RECIPIENT_EMAIL` | qotmdgkr@gmail.com |
| `KAKAO_REST_API_KEY` | 카카오 REST API 앱 키 |
| `KAKAO_REFRESH_TOKEN` | 카카오 refresh token |
| `NEWSAPI_KEY` | NewsAPI.org API Key (선택) |

---

## 6. GitHub Actions 워크플로우

### 6.1 이메일 워크플로우 (`.github/workflows/email_briefing.yml`)
```yaml
name: Daily Email Briefing
on:
  schedule:
    - cron: '35 21 * * *'   # 매일 KST 06:35
  workflow_dispatch:          # 수동 실행 가능
jobs:
  send-email:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: pip install -r requirements.txt
      - run: python src/price_fetcher.py && python src/news_fetcher.py && python src/briefing_builder.py && python src/email_sender.py
        env:
          GMAIL_SENDER: ${{ secrets.GMAIL_SENDER }}
          GMAIL_APP_PASSWORD: ${{ secrets.GMAIL_APP_PASSWORD }}
          RECIPIENT_EMAIL: ${{ secrets.RECIPIENT_EMAIL }}
          NEWSAPI_KEY: ${{ secrets.NEWSAPI_KEY }}
```

### 6.2 카카오톡 워크플로우 (`.github/workflows/kakao_briefing.yml`)
```yaml
name: Daily KakaoTalk Briefing
on:
  schedule:
    - cron: '39 21 * * *'   # 매일 KST 06:39
  workflow_dispatch:
jobs:
  send-kakao:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: pip install -r requirements.txt
      - run: python src/price_fetcher.py && python src/news_fetcher.py && python src/briefing_builder.py && python src/kakao_sender.py
        env:
          KAKAO_REST_API_KEY: ${{ secrets.KAKAO_REST_API_KEY }}
          KAKAO_REFRESH_TOKEN: ${{ secrets.KAKAO_REFRESH_TOKEN }}
          NEWSAPI_KEY: ${{ secrets.NEWSAPI_KEY }}
```

---

## 7. cron-job.org 연동

> **역할**: GitHub Actions 자체 스케줄(`schedule`) 트리거는 레포지토리 활동이 없으면 비활성화될 수 있어 신뢰도가 낮음. cron-job.org에서 GitHub Actions `workflow_dispatch` REST API를 직접 호출하여 보장.

### 7.1 설정 방법
1. cron-job.org 가입 후 새 Job 생성
2. **URL**: `https://api.github.com/repos/{owner}/{repo}/actions/workflows/email_briefing.yml/dispatches`
3. **Method**: POST
4. **Headers**:
   - `Authorization: Bearer {GITHUB_PAT}`
   - `Accept: application/vnd.github+json`
   - `Content-Type: application/json`
5. **Body**: `{"ref":"main"}`
6. **Schedule**: `35 21 * * *` (이메일), `39 21 * * *` (카카오)

---

## 8. 구현 우선순위 및 마일스톤

| 단계 | 내용 | 예상 기간 |
|------|------|---------|
| M1 | 가격 수집 (pykrx + yfinance) + 콘솔 출력 검증 | 1일 |
| M2 | 뉴스 수집 (RSS + 번역) 검증 | 1일 |
| M3 | 브리핑 조합 + HTML/텍스트 포맷 | 1일 |
| M4 | 이메일 발송 연동 + GitHub Actions 등록 | 1일 |
| M5 | 카카오톡 발송 연동 + cron-job.org 등록 | 1일 |
| M6 | 테스트, 오류 처리, 공휴일 대응 | 1일 |

---

## 9. 제약 및 고려사항

- pykrx는 KRX 데이터를 가져오며, 당일 장 마감(15:30 KST) 이후에만 당일 종가 확정됨. 06:35 발송 시에는 **전일 종가** 기준으로 브리핑
- yfinance 해외 종가는 미국 시장 마감(동부 16:00 = KST 익일 05:00) 이후 확정됨. 06:35 발송 시 당일 미국 종가 기준 사용 가능
- 카카오 `access_token` 유효기간 6시간 → 매 실행마다 `refresh_token`으로 재발급 필요
- GitHub Actions 무료 플랜: 월 2,000분 제한 (1회 약 2-3분 소요, 60회/월 → 여유 있음)
- 뉴스 없는 종목은 "오늘 관련 뉴스 없음" 표시 (에러 없이 처리)
