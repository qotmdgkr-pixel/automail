#!/usr/bin/env python3
"""포트폴리오 뉴스 수집 — Google News RSS (메인) + NewsAPI (폴백)
번역: deep_translator GoogleTranslator (영→한)
출력: data/news.json
"""

import json
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote_plus

import feedparser
import requests
from deep_translator import GoogleTranslator

from config import KR_ETFS, US_STOCKS

DATA_DIR = Path(__file__).parent.parent / "data"
MAX_NEWS = 3
RSS_DELAY = 1.2   # Google News RSS 레이트 리밋 방지 (초)
KST = timezone(timedelta(hours=9))

# ── 미국 주식: 국내 한글 검색어 ──────────────────────────────────────────────
US_DOMESTIC_QUERY = {
    "AMZN": "아마존 주가",
    "AVGO": "브로드컴 주가",
    "GOOGL": "알파벳 구글 주가",
    "META": "메타플랫폼스 주가",
    "MSFT": "마이크로소프트 주가",
    "NVDA": "엔비디아 주가",
    "QQQ": "QQQ 나스닥100 ETF",
    "TSLA": "테슬라 주가",
}

# ── 국내 ETF: 해외 영문 검색어 (기초지수/자산 중심) ─────────────────────────
KR_INTL_QUERY = {
    "458730": "US dividend Dow Jones stocks",
    "305080": "US Treasury 10 year bond futures",
    "411060": "gold price KRX Korea",
    "195930": "S&P500 index ETF",
    "447770": "US dividend stocks hedged Korea ETF",
    "479850": "US high yield bond ETF",
    "453850": "US dollar SOFR interest rate",
    "449180": "Korea bank dividend stocks",
    "432620": "Korea REIT real estate infrastructure",
    "475080": "Korea value up stocks KRX",
}


# ── 날짜 유틸 ────────────────────────────────────────────────────────────────

def today_kst() -> str:
    return datetime.now(KST).strftime("%Y-%m-%d")


def is_recent(entry, days: int = 2) -> bool:
    """최근 N일 이내 기사인지 확인 (날짜 파싱 실패 시 포함)"""
    for attr in ("published_parsed", "updated_parsed"):
        t = getattr(entry, attr, None)
        if t:
            try:
                pub = datetime(*t[:6], tzinfo=timezone.utc)
                cutoff = datetime.now(timezone.utc) - timedelta(days=days)
                return pub >= cutoff
            except Exception:
                pass
    return True


def parse_published(entry) -> str:
    for attr in ("published_parsed", "updated_parsed"):
        t = getattr(entry, attr, None)
        if t:
            try:
                return (datetime(*t[:6], tzinfo=timezone.utc)
                        .astimezone(KST).strftime("%Y-%m-%d"))
            except Exception:
                pass
    return today_kst()


# ── Google News RSS ──────────────────────────────────────────────────────────

def fetch_rss(query: str, lang: str = "en") -> list:
    """Google News RSS 파싱. lang='ko' → 한국어, 'en' → 영어"""
    if lang == "ko":
        url = (f"https://news.google.com/rss/search"
               f"?q={quote_plus(query)}&hl=ko&gl=KR&ceid=KR:ko")
    else:
        url = (f"https://news.google.com/rss/search"
               f"?q={quote_plus(query)}&hl=en-US&gl=US&ceid=US:en")
    try:
        feed = feedparser.parse(url)
        items, seen = [], set()
        for entry in feed.entries:
            if not is_recent(entry):
                continue
            link = getattr(entry, "link", "")
            if link in seen:
                continue
            seen.add(link)
            source = ""
            if hasattr(entry, "source") and hasattr(entry.source, "title"):
                source = entry.source.title
            items.append({
                "title": entry.get("title", "").strip(),
                "url": link,
                "source": source,
                "published": parse_published(entry),
                "summary": getattr(entry, "summary", ""),
            })
            if len(items) >= MAX_NEWS:
                break
        return items
    except Exception:
        return []


# ── NewsAPI 폴백 ─────────────────────────────────────────────────────────────

def fetch_newsapi(query: str, api_key: str) -> list:
    """NewsAPI.org 영문 뉴스 (API 키 있을 때만 호출)"""
    try:
        from_date = (datetime.now(timezone.utc) - timedelta(days=2)).strftime("%Y-%m-%d")
        r = requests.get(
            "https://newsapi.org/v2/everything",
            params={
                "q": query,
                "from": from_date,
                "sortBy": "publishedAt",
                "language": "en",
                "pageSize": MAX_NEWS,
                "apiKey": api_key,
            },
            timeout=10,
        )
        items = []
        for art in r.json().get("articles", []):
            items.append({
                "title": (art.get("title") or "").strip(),
                "url": art.get("url", ""),
                "source": (art.get("source") or {}).get("name", ""),
                "published": (art.get("publishedAt") or "")[:10],
                "summary": art.get("description") or "",
            })
        return items
    except Exception:
        return []


# ── 번역 ─────────────────────────────────────────────────────────────────────

def translate_text(text: str) -> str:
    """영→한 번역. 실패 시 원문 반환"""
    if not text:
        return text
    try:
        return GoogleTranslator(source="en", target="ko").translate(text[:500])
    except Exception:
        return text


# ── 종목별 수집 헬퍼 ─────────────────────────────────────────────────────────

def _to_intl(raw: list) -> list:
    return [
        {
            "title": translate_text(d["title"]),
            "title_original": d["title"],
            "url": d["url"],
            "source": d["source"],
            "published": d["published"],
        }
        for d in raw
    ]


def fetch_news_for_us(ticker: str, name_kr: str, newsapi_key: str = "") -> dict:
    """미국 주식: 국내 한글 뉴스 + 해외 영문 뉴스(번역)"""
    domestic_raw = fetch_rss(US_DOMESTIC_QUERY.get(ticker, f"{name_kr} 주가"), lang="ko")
    domestic = [{"title": d["title"], "url": d["url"],
                 "source": d["source"], "published": d["published"]}
                for d in domestic_raw]
    time.sleep(RSS_DELAY)

    intl_raw = fetch_rss(f"{ticker} stock", lang="en")
    if not intl_raw and newsapi_key:
        intl_raw = fetch_newsapi(f"{ticker} stock", newsapi_key)
    international = _to_intl(intl_raw)
    time.sleep(RSS_DELAY)

    return {"domestic": domestic, "international": international}


def fetch_news_for_kr(code: str, display: str, newsapi_key: str = "") -> dict:
    """국내 ETF: 국내 한글 뉴스 + 해외 영문 뉴스(번역)"""
    domestic_raw = fetch_rss(display, lang="ko")
    domestic = [{"title": d["title"], "url": d["url"],
                 "source": d["source"], "published": d["published"]}
                for d in domestic_raw]
    time.sleep(RSS_DELAY)

    intl_q = KR_INTL_QUERY.get(code, display)
    intl_raw = fetch_rss(intl_q, lang="en")
    if not intl_raw and newsapi_key:
        intl_raw = fetch_newsapi(intl_q, newsapi_key)
    international = _to_intl(intl_raw)
    time.sleep(RSS_DELAY)

    return {"domestic": domestic, "international": international}


# ── 전체 수집 ────────────────────────────────────────────────────────────────

def fetch_all_news() -> dict:
    newsapi_key = os.getenv("NEWSAPI_KEY", "")
    items: dict = {}
    total = len(US_STOCKS) + len(KR_ETFS)
    idx = 0

    for name_kr, ticker in US_STOCKS.items():
        idx += 1
        print(f"  [{idx:2d}/{total}] {name_kr} ({ticker})", flush=True)
        try:
            news = fetch_news_for_us(ticker, name_kr, newsapi_key)
            items[ticker] = {"name": name_kr, **news}
            print(f"           국내 {len(news['domestic'])}건 / 해외 {len(news['international'])}건")
        except Exception as e:
            print(f"           오류: {e}")
            items[ticker] = {"name": name_kr, "domestic": [], "international": []}

    for etf in KR_ETFS:
        idx += 1
        code, display = etf["code"], etf["display"]
        print(f"  [{idx:2d}/{total}] {display} ({code})", flush=True)
        try:
            news = fetch_news_for_kr(code, display, newsapi_key)
            items[code] = {"name": display, **news}
            print(f"           국내 {len(news['domestic'])}건 / 해외 {len(news['international'])}건")
        except Exception as e:
            print(f"           오류: {e}")
            items[code] = {"name": display, "domestic": [], "international": []}

    return {
        "fetched_at": datetime.now().isoformat(timespec="seconds"),
        "date": today_kst(),
        "items": items,
    }


def save_news(news_data: dict):
    DATA_DIR.mkdir(exist_ok=True)
    path = DATA_DIR / "news.json"
    path.write_text(json.dumps(news_data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n  저장 완료: {path}")


def main():
    print(f"\n뉴스 수집 시작 ({today_kst()}) ...\n")
    news_data = fetch_all_news()
    save_news(news_data)

    items = news_data["items"]
    total_d = sum(len(v["domestic"]) for v in items.values())
    total_i = sum(len(v["international"]) for v in items.values())
    print(f"\n  완료: 국내 총 {total_d}건 / 해외 총 {total_i}건 ({len(items)}종목)")


if __name__ == "__main__":
    main()
