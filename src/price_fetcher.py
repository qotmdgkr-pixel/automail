#!/usr/bin/env python3
"""포트폴리오 종가 조회 — yfinance(미국) + FinanceDataReader(국내 ETF)
출력: 콘솔 테이블 + data/prices.json
"""

import json
from datetime import datetime, timedelta
from pathlib import Path

import FinanceDataReader as fdr
import yfinance as yf

from config import KR_ETFS, US_STOCKS

DATA_DIR = Path(__file__).parent.parent / "data"


def recent_close_date() -> str:
    """가장 최근 거래일 (오늘 포함, YYYY-MM-DD)"""
    d = datetime.now()
    while d.weekday() >= 5:
        d -= timedelta(days=1)
    return d.strftime("%Y-%m-%d")


def fetch_us() -> list:
    """미국 주식 종가 + 등락률 수집 (yfinance)"""
    rows = []
    for name, sym in US_STOCKS.items():
        try:
            info = yf.Ticker(sym).fast_info
            price = round(info.last_price, 2)
            prev_close = round(info.previous_close, 2)
            change_pct = round((price - prev_close) / prev_close * 100, 2) if prev_close else None
            rows.append({
                "name": name, "ticker": sym,
                "price": price, "change_pct": change_pct,
                "ok": True,
            })
        except Exception as e:
            rows.append({
                "name": name, "ticker": sym,
                "price": None, "change_pct": None,
                "ok": False, "err": str(e),
            })
    return rows


def fetch_kr() -> list:
    """국내 ETF 종가 + 등락률 수집 (FinanceDataReader)"""
    date = recent_close_date()
    start = (datetime.strptime(date, "%Y-%m-%d") - timedelta(days=10)).strftime("%Y-%m-%d")

    rows = []
    for etf in KR_ETFS:
        display = etf["display"]
        code = etf["code"]
        try:
            df = fdr.DataReader(code, start, date)
            if df is None or df.empty:
                raise ValueError("데이터 없음")
            close_today = int(df["Close"].iloc[-1])
            change_pct = round(float(df["Change"].iloc[-1]) * 100, 2) if "Change" in df.columns else None
            rows.append({
                "name": display, "ticker": code,
                "price": close_today, "change_pct": change_pct,
                "ok": True,
            })
        except Exception as e:
            rows.append({
                "name": display, "ticker": code,
                "price": None, "change_pct": None,
                "ok": False, "err": str(e),
            })
    return rows


def print_results(us: list, kr: list):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    W = 72
    print(f"\n{'━' * W}")
    print(f"  포트폴리오 종가   ({now})")
    print(f"{'━' * W}")

    print(f"\n  ▶ 미국 주식 (USD)")
    print(f"  {'─' * 68}")
    print(f"  {'종목명':<22} {'티커':<6}  {'현재가':>14}  {'등락률':>8}")
    print(f"  {'─' * 68}")
    for r in us:
        if r["ok"]:
            pct_val = r["change_pct"] or 0
            arrow = "▲" if pct_val >= 0 else "▼"
            pct = f"{arrow}{abs(pct_val):+.2f}%"
            print(f"  {r['name']:<22} {r['ticker']:<6}  ${r['price']:>13,.2f}  {pct:>8}")
        else:
            print(f"  {r['name']:<22} {r['ticker']:<6}  {'조회 실패':>14}")

    print(f"\n  ▶ 국내 ETF (KRW)")
    print(f"  {'─' * 68}")
    print(f"  {'종목명':<32} {'코드':<7} {'현재가':>11}  {'등락률':>8}")
    print(f"  {'─' * 68}")
    for r in kr:
        ticker = r.get("ticker") or "N/A"
        if r["ok"]:
            pct_val = r["change_pct"] or 0
            arrow = "▲" if pct_val >= 0 else "▼"
            pct = f"{arrow}{abs(pct_val):+.2f}%"
            print(f"  {r['name']:<32} {ticker:<7} {r['price']:>10,}원  {pct:>8}")
        else:
            err = r.get("err", "오류")
            print(f"  {r['name']:<32} {ticker:<7} {err:>11}")

    print(f"\n{'━' * W}\n")


def save_prices(us: list, kr: list):
    """data/prices.json 저장"""
    DATA_DIR.mkdir(exist_ok=True)
    data = {
        "fetched_at": datetime.now().isoformat(timespec="seconds"),
        "date": datetime.now().strftime("%Y-%m-%d"),
        "us": us,
        "kr": kr,
    }
    path = DATA_DIR / "prices.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  → 저장 완료: {path}")


def main():
    print("미국 주식 조회 중...", flush=True)
    us = fetch_us()

    print("국내 ETF 조회 중...", flush=True)
    kr = fetch_kr()

    print_results(us, kr)
    save_prices(us, kr)


if __name__ == "__main__":
    main()
