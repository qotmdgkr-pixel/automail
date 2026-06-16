#!/usr/bin/env python3
"""포트폴리오 자동 브리핑 — 통합 실행 스크립트
사용법:
  python src/main.py              # 이메일 + 카카오 모두 발송
  python src/main.py --mode email # 이메일만
  python src/main.py --mode kakao # 카카오톡만
"""

import argparse
import sys
import traceback
from datetime import datetime

# Windows cp949 환경에서 유니코드 출력 보장
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')


def _run(label: str, fn) -> bool:
    print(f"\n{'─'*50}")
    print(f"  [{label}] 시작")
    print(f"{'─'*50}")
    try:
        fn()
        print(f"  [{label}] 완료 [OK]")
        return True
    except SystemExit as e:
        code = e.code if isinstance(e.code, int) else 1
        print(f"  [{label}] 종료 (exit {code})", file=sys.stderr)
        return code == 0
    except Exception:
        traceback.print_exc()
        print(f"  [{label}] 실패 [FAIL]", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        choices=["all", "email", "kakao"],
        default="all",
        help="발송 대상 (기본값: all)",
    )
    args = parser.parse_args()

    start = datetime.now()
    print(f"\n{'━'*50}")
    print(f"  포트폴리오 브리핑 자동 실행  ({start.strftime('%Y-%m-%d %H:%M')})")
    print(f"  모드: {args.mode}")
    print(f"{'━'*50}")

    # sys.path에 src 추가 (모듈 import 보장)
    import os
    src_dir = os.path.dirname(os.path.abspath(__file__))
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)

    import price_fetcher
    import news_fetcher
    import briefing_builder
    import email_sender
    import kakao_sender

    results = {}

    # Step 1-3: 데이터 수집 + 브리핑 생성 (항상 실행)
    results["가격 수집"]    = _run("가격 수집",    price_fetcher.main)
    results["뉴스 수집"]    = _run("뉴스 수집",    news_fetcher.main)
    results["브리핑 생성"]  = _run("브리핑 생성",  briefing_builder.main)

    # Step 4-5: 발송 (모드에 따라)
    if args.mode in ("all", "email"):
        results["이메일 발송"] = _run("이메일 발송", email_sender.main)

    if args.mode in ("all", "kakao"):
        results["카카오 발송"] = _run("카카오 발송", kakao_sender.main)

    # 결과 요약
    elapsed = (datetime.now() - start).seconds
    print(f"\n{'━'*50}")
    print(f"  실행 결과 요약  (소요: {elapsed}초)")
    print(f"{'━'*50}")
    all_ok = True
    for step, ok in results.items():
        status = "[OK]" if ok else "[NG]"
        print(f"  {status}  {step}")
        if not ok:
            all_ok = False
    print(f"{'━'*50}\n")

    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
