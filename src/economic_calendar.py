#!/usr/bin/env python3
"""경제 지표 발표 일정 수집 — Forex Factory 공개 JSON API
출력: data/economic_calendar.json
"""

import json
from datetime import datetime
from pathlib import Path
from urllib import request, error

DATA_DIR = Path(__file__).parent.parent / "data"
FF_CALENDAR_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"

# 관련 통화 코드 (Forex Factory 기준)
RELEVANT_COUNTRIES = {"USD", "KRW"}
# High/Medium 영향도 이벤트만
RELEVANT_IMPACT = {"High", "Medium"}


def fetch_raw_calendar() -> list:
    """이번 주 경제 지표 원본 JSON 수집"""
    req = request.Request(
        FF_CALENDAR_URL,
        headers={"User-Agent": "Mozilla/5.0 (compatible; portfolio-briefing/1.0)"},
    )
    try:
        with request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as e:
        print(f"[calendar] HTTP {e.code}: {e.reason}", flush=True)
        return []
    except Exception as e:
        print(f"[calendar] 수집 실패: {e}", flush=True)
        return []


def _parse_date(date_str: str) -> str:
    """'Jun 18, 2026' → '2026-06-18'  (파싱 실패 시 빈 문자열)"""
    for fmt in ("%b %d, %Y", "%B %d, %Y"):
        try:
            return datetime.strptime(date_str.strip(), fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return ""


def _build_entry(raw: dict) -> dict:
    return {
        "title":    raw.get("title", "").strip(),
        "country":  raw.get("country", ""),
        "date":     _parse_date(raw.get("date", "")),
        "time":     raw.get("time", ""),
        "impact":   raw.get("impact", ""),
        "forecast": raw.get("forecast", ""),
        "previous": raw.get("previous", ""),
    }


def main():
    today = datetime.now().strftime("%Y-%m-%d")
    print(f"[calendar] 경제 지표 캘린더 수집 중... (기준일: {today})", flush=True)

    raw_list = fetch_raw_calendar()

    today_events = []
    week_events  = []

    for raw in raw_list:
        country = raw.get("country", "")
        impact  = raw.get("impact", "")
        if country not in RELEVANT_COUNTRIES:
            continue
        if impact not in RELEVANT_IMPACT:
            continue

        entry = _build_entry(raw)
        if entry["date"] == today:
            today_events.append(entry)
        week_events.append(entry)

    result = {
        "fetched_at": datetime.now().isoformat(timespec="seconds"),
        "today":     today_events,
        "this_week": week_events,
    }

    DATA_DIR.mkdir(exist_ok=True)
    path = DATA_DIR / "economic_calendar.json"
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[calendar] 오늘 {len(today_events)}건 / 이번 주 {len(week_events)}건 → {path}", flush=True)


if __name__ == "__main__":
    main()
