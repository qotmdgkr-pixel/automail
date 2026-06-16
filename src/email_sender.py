#!/usr/bin/env python3
"""Gmail SMTP 이메일 발송 — data/briefing_email.html → qotmdgkr@gmail.com"""

import os
import smtplib
import sys
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"


def load_env():
    """로컬 .env 파일 로드 (있을 때만). GitHub Actions에서는 OS 환경변수 사용."""
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
        print(f"[email] 오류: 환경변수 {key} 가 설정되지 않았습니다.", file=sys.stderr)
        sys.exit(1)
    return val


def send_email(subject: str, html_body: str, text_body: str) -> bool:
    sender    = _require("GMAIL_SENDER")
    password  = _require("GMAIL_APP_PASSWORD")
    to_raw    = _require("RECIPIENT_EMAIL")
    to_list   = [addr.strip() for addr in to_raw.split(",") if addr.strip()]

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = sender
    msg["To"]      = ", ".join(to_list)

    msg.attach(MIMEText(text_body, "plain",  "utf-8"))
    msg.attach(MIMEText(html_body, "html",   "utf-8"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            smtp.login(sender, password)
            smtp.sendmail(sender, to_list, msg.as_bytes())
        print(f"[email] 발송 완료 → {', '.join(to_list)}")
        return True
    except smtplib.SMTPAuthenticationError:
        print("[email] 오류: Gmail 인증 실패. 앱 비밀번호를 확인하세요.", file=sys.stderr)
        return False
    except Exception as e:
        print(f"[email] 오류: {e}", file=sys.stderr)
        return False


def main():
    load_env()

    html_path = DATA_DIR / "briefing_email.html"
    text_path = DATA_DIR / "briefing_kakao.txt"

    if not html_path.exists():
        print("[email] 오류: briefing_email.html 없음. briefing_builder.py를 먼저 실행하세요.", file=sys.stderr)
        sys.exit(1)

    html_body = html_path.read_text(encoding="utf-8")
    text_body = text_path.read_text(encoding="utf-8") if text_path.exists() else ""

    date    = datetime.now().strftime("%Y-%m-%d")
    subject = f"[포트폴리오 브리핑] {date} 종가 및 주요 뉴스"

    ok = send_email(subject, html_body, text_body)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
