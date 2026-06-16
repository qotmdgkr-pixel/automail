#!/usr/bin/env python3
"""카카오톡 나에게 보내기 — data/briefing_kakao.txt → KakaoTalk"""

import json
import os
import sys
from pathlib import Path
from urllib import request, parse, error

DATA_DIR = Path(__file__).parent.parent / "data"
KAKAO_TOKEN_URL   = "https://kauth.kakao.com/oauth/token"
KAKAO_MESSAGE_URL = "https://kapi.kakao.com/v2/api/talk/memo/default/send"


def load_env():
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        try:
            from dotenv import load_dotenv
            load_dotenv(env_path, override=False)
        except ImportError:
            pass


def _require(key: str) -> str:
    val = os.getenv(key, "").strip()
    if not val:
        print(f"[kakao] 오류: 환경변수 {key} 가 설정되지 않았습니다.", file=sys.stderr)
        sys.exit(1)
    return val


def get_access_token(rest_api_key: str, refresh_token: str) -> str:
    """refresh_token으로 access_token 재발급"""
    payload = parse.urlencode({
        "grant_type":    "refresh_token",
        "client_id":     rest_api_key,
        "refresh_token": refresh_token,
    }).encode("utf-8")

    req = request.Request(
        KAKAO_TOKEN_URL,
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"[kakao] 토큰 재발급 실패 HTTP {e.code}: {body}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"[kakao] 토큰 재발급 오류: {e}", file=sys.stderr)
        sys.exit(1)

    access_token = data.get("access_token", "")
    if not access_token:
        print(f"[kakao] 토큰 재발급 실패: {data}", file=sys.stderr)
        sys.exit(1)

    # refresh_token도 갱신된 경우 안내
    if data.get("refresh_token"):
        print("[kakao] 새 refresh_token 발급됨 — .env / GitHub Secrets 업데이트 필요:")
        print(f"  KAKAO_REFRESH_TOKEN={data['refresh_token']}")

    return access_token


def send_kakao_message(access_token: str, text: str) -> bool:
    """카카오톡 나에게 보내기 (텍스트 타입)"""
    if len(text) > 2000:
        text = text[:1900] + "\n...(생략)"

    template = json.dumps(
        {
            "object_type": "text",
            "text": text,
            "link": {"web_url": "", "mobile_web_url": ""},
        },
        ensure_ascii=False,
    )
    payload = parse.urlencode({"template_object": template}).encode("utf-8")

    req = request.Request(
        KAKAO_MESSAGE_URL,
        data=payload,
        headers={
            "Authorization":  f"Bearer {access_token}",
            "Content-Type":   "application/x-www-form-urlencoded;charset=utf-8",
        },
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("result_code") == 0:
                print("[kakao] 발송 완료")
                return True
            print(f"[kakao] 발송 실패: {data}", file=sys.stderr)
            return False
    except error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"[kakao] 발송 실패 HTTP {e.code}: {body}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"[kakao] 발송 오류: {e}", file=sys.stderr)
        return False


def main():
    load_env()

    txt_path = DATA_DIR / "briefing_kakao.txt"
    if not txt_path.exists():
        print("[kakao] 오류: briefing_kakao.txt 없음. briefing_builder.py를 먼저 실행하세요.", file=sys.stderr)
        sys.exit(1)

    text = txt_path.read_text(encoding="utf-8")

    rest_api_key  = _require("KAKAO_REST_API_KEY")
    refresh_token = _require("KAKAO_REFRESH_TOKEN")

    print("[kakao] access_token 재발급 중...")
    access_token = get_access_token(rest_api_key, refresh_token)

    print(f"[kakao] 메시지 발송 중... ({len(text)}자)")
    ok = send_kakao_message(access_token, text)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
