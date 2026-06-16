#!/usr/bin/env python3
"""카카오 refresh_token 발급 — 로컬 서버로 자동 캡처 (타이밍 문제 없음)
실행: python get_kakao_token.py
사전 설정: 카카오 디벨로퍼스 → Redirect URI 에 http://localhost:5000 추가
"""

import json
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib import parse, request as urllib_request, error

REST_API_KEY  = "16dbae1853c5caf130908c75e4346c1f"
REDIRECT_URI  = "http://localhost:5000"
PORT          = 5000

AUTH_URL = (
    f"https://kauth.kakao.com/oauth/authorize"
    f"?client_id={REST_API_KEY}"
    f"&redirect_uri={parse.quote(REDIRECT_URI, safe='')}"
    f"&response_type=code"
    f"&scope=talk_message"
)

received_code = None


def exchange_code(code: str) -> dict:
    payload = parse.urlencode({
        "grant_type":   "authorization_code",
        "client_id":    REST_API_KEY,
        "redirect_uri": REDIRECT_URI,
        "code":         code,
    }).encode("utf-8")
    req = urllib_request.Request(
        "https://kauth.kakao.com/oauth/token",
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urllib_request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def update_env(key: str, value: str):
    env_path = Path(__file__).parent / ".env"
    if not env_path.exists():
        return
    lines = env_path.read_text(encoding="utf-8").splitlines()
    updated, found = [], False
    for line in lines:
        if line.startswith(f"{key}="):
            updated.append(f"{key}={value}")
            found = True
        else:
            updated.append(line)
    if not found:
        updated.append(f"{key}={value}")
    env_path.write_text("\n".join(updated) + "\n", encoding="utf-8")


class CallbackHandler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # 서버 로그 숨김

    def do_GET(self):
        global received_code
        qs = parse.parse_qs(parse.urlparse(self.path).query)
        code = qs.get("code", [""])[0]

        if code:
            received_code = code
            print(f"\n  [✓] 인가 코드 수신: {code[:20]}...")
            print("  [→] 토큰 교환 중...")

            try:
                data = exchange_code(code)
                access_token  = data.get("access_token", "")
                refresh_token = data.get("refresh_token", "")

                if access_token:
                    print(f"\n  발급 완료!")
                    print(f"  access_token  : {access_token[:30]}...")
                    if refresh_token:
                        print(f"  refresh_token : {refresh_token[:30]}...")
                        update_env("KAKAO_REFRESH_TOKEN", refresh_token)
                        print("\n  .env 자동 업데이트 완료!")
                    else:
                        print("  [참고] refresh_token 없음 → access_token을 사용합니다.")
                        update_env("KAKAO_REFRESH_TOKEN", access_token)

                    self._respond("토큰 발급 성공! 이 창을 닫아도 됩니다.")
                else:
                    print(f"  [✗] 토큰 발급 실패: {data}")
                    self._respond(f"토큰 발급 실패: {data}")
            except Exception as ex:
                print(f"  [✗] 오류: {ex}")
                self._respond(f"오류: {ex}")
        else:
            error = qs.get("error", [""])[0]
            print(f"\n  [✗] 오류 응답: {error}")
            self._respond(f"오류: {error}")

        # 서버 종료 (별도 스레드)
        threading.Thread(target=self.server.shutdown, daemon=True).start()

    def _respond(self, msg: str):
        body = f"<html><body style='font-family:sans-serif;padding:40px'><h2>{msg}</h2></body></html>"
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(body.encode("utf-8"))


def main():
    print("=" * 55)
    print("  카카오 Refresh Token 자동 발급")
    print("=" * 55)
    print(f"\n  로컬 서버 시작 (포트 {PORT})...")

    server = HTTPServer(("localhost", PORT), CallbackHandler)

    print("  브라우저를 열어 카카오 로그인 화면으로 이동합니다...")
    webbrowser.open(AUTH_URL)

    print("  로그인 완료 후 자동으로 토큰이 발급됩니다.\n")
    server.serve_forever()

    print(f"\n  완료! 이제 python src/kakao_sender.py 를 실행하세요.")


if __name__ == "__main__":
    main()
