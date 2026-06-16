# 포트폴리오 자동 브리핑 시스템

매일 아침 미국 주식 8종 + 국내 ETF 10종의 전일 종가와 주요 뉴스를 이메일과 카카오톡으로 자동 발송합니다.

---

## 필요한 GitHub Secrets

| Secret 이름 | 설명 |
|---|---|
| `GMAIL_SENDER` | 발송자 Gmail 주소 (예: yourname@gmail.com) |
| `GMAIL_APP_PASSWORD` | Gmail 앱 비밀번호 (16자리, 공백 포함) |
| `RECIPIENT_EMAIL` | 수신자 이메일 주소 |
| `KAKAO_REST_API_KEY` | 카카오 REST API 키 |
| `KAKAO_REFRESH_TOKEN` | 카카오 리프레시 토큰 |
| `NEWSAPI_KEY` | NewsAPI 키 (선택 사항, 없으면 Google News RSS만 사용) |

**등록 방법:** GitHub 저장소 → Settings → Secrets and variables → Actions → New repository secret

---

## cron-job.org 설정 방법

GitHub Actions의 schedule 트리거는 지연이 생길 수 있으므로, cron-job.org를 통해 `workflow_dispatch`로 정확한 시간에 실행합니다.

1. [cron-job.org](https://cron-job.org) 가입 후 **New Cronjob** 생성
2. 이메일 브리핑 설정:
   - **URL:** `https://api.github.com/repos/qotmdgkr-pixel/automail/actions/workflows/email_briefing.yml/dispatches`
   - **Method:** POST
   - **Headers:**
     ```
     Authorization: Bearer {GITHUB_PAT}
     Accept: application/vnd.github+json
     Content-Type: application/json
     ```
   - **Body:** `{"ref":"main"}`
   - **Schedule:** `35 21 * * *` (UTC) = KST 06:35
3. 카카오 브리핑도 동일하게 설정:
   - URL의 `email_briefing.yml` → `kakao_briefing.yml`로 변경
   - **Schedule:** `39 21 * * *` (UTC) = KST 06:39

**GitHub PAT 발급:** Settings → Developer settings → Personal access tokens → Fine-grained tokens → `workflow` 권한 부여

---

## 로컬 실행 방법

```bash
pip install -r requirements.txt
cp .env.example .env   # .env에 실제 값 입력
python src/main.py              # 이메일 + 카카오 모두 발송
python src/main.py --mode email # 이메일만
python src/main.py --mode kakao # 카카오톡만
```
