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

_INDEX_LIST = [
    {"name": "S&P 500", "ticker": "^GSPC"},
    {"name": "NASDAQ",  "ticker": "^IXIC"},
    {"name": "KOSPI",   "ticker": "^KS11"},
    {"name": "KOSDAQ",  "ticker": "^KQ11"},
]


def recent_close_date() -> str:
    """가장 최근 거래일 (오늘 포함, YYYY-MM-DD)"""
    d = datetime.now()
    while d.weekday() >= 5:
        d -= timedelta(days=1)
    return d.strftime("%Y-%m-%d")


def fetch_fx() -> dict:
    """USD/KRW 환율 조회"""
    try:
        info = yf.Ticker("USDKRW=X").fast_info
        rate = round(info.last_price, 2)
        prev = info.previous_close
        change_pct = round((rate - prev) / prev * 100, 2) if prev else None
        return {"rate": rate, "change_pct": change_pct, "ok": True}
    except Exception as e:
        return {"rate": None, "change_pct": None, "ok": False, "err": str(e)}


def fetch_indices() -> list:
    """주요 지수 조회 (S&P500, NASDAQ, KOSPI, KOSDAQ)"""
    rows = []
    for idx in _INDEX_LIST:
        try:
            info = yf.Ticker(idx["ticker"]).fast_info
            price = round(info.last_price, 2)
            prev  = info.previous_close
            change_pct = round((price - prev) / prev * 100, 2) if prev else None
            rows.append({
                "name": idx["name"], "ticker": idx["ticker"],
                "price": price, "change_pct": change_pct, "ok": True,
            })
        except Exception as e:
            rows.append({
                "name": idx["name"], "ticker": idx["ticker"],
                "price": None, "change_pct": None,
                "ok": False, "err": str(e),
            })
    return rows


def fetch_us() -> list:
    """미국 주식 종가 + 등락률 + 52주범위 수집 (yfinance)"""
    rows = []
    for name, sym in US_STOCKS.items():
        try:
            info = yf.Ticker(sym).fast_info
            price      = round(info.last_price, 2)
            prev_close = round(info.previous_close, 2)
            change_pct = round((price - prev_close) / prev_close * 100, 2) if prev_close else None
            w52_high   = round(getattr(info, "fifty_two_week_high", None) or 0, 2) or None
            w52_low    = round(getattr(info, "fifty_two_week_low",  None) or 0, 2) or None
            rows.append({
                "name": name, "ticker": sym,
                "price": price, "change_pct": change_pct,
                "week52_high": w52_high, "week52_low": w52_low,
                "ok": True,
            })
        except Exception as e:
            rows.append({
                "name": name, "ticker": sym,
                "price": None, "change_pct": None,
                "week52_high": None, "week52_low": None,
                "ok": False, "err": str(e),
            })
    return rows


def _fetch_kr_pykrx(code: str, date: str) -> dict:
    """pykrx로 ETF 종가+등락률 조회 (FDR 폴백용)"""
    from pykrx import stock as pkrx
    start_str = (datetime.strptime(date, "%Y-%m-%d") - timedelta(days=10)).strftime("%Y%m%d")
    date_str = date.replace("-", "")
    df = pkrx.get_etf_ohlcv_by_date(start_str, date_str, code)
    if df is None or df.empty:
        raise ValueError("pykrx 데이터 없음")
    close_today = int(df["종가"].iloc[-1])
    if len(df) >= 2:
        prev = int(df["종가"].iloc[-2])
        change_pct = round((close_today - prev) / prev * 100, 2) if prev else None
    else:
        change_pct = None
    return {"price": close_today, "change_pct": change_pct}


def fetch_kr() -> list:
    """국내 ETF 종가 + 등락률 + 52주범위 수집 (FinanceDataReader, pykrx 폴백)"""
    date      = recent_close_date()
    start_1yr = (datetime.strptime(date, "%Y-%m-%d") - timedelta(days=400)).strftime("%Y-%m-%d")

    rows = []
    for etf in KR_ETFS:
        display = etf["display"]
        code    = etf["code"]
        try:
            df = fdr.DataReader(code, start_1yr, date)
            if df is None or df.empty:
                raise ValueError("데이터 없음")
            close_today = int(df["Close"].iloc[-1])
            change_pct  = round(float(df["Change"].iloc[-1]) * 100, 2) if "Change" in df.columns else None
            w52_high    = int(df["Close"].max())
            w52_low     = int(df["Close"].min())
            rows.append({
                "name": display, "ticker": code,
                "price": close_today, "change_pct": change_pct,
                "week52_high": w52_high, "week52_low": w52_low,
                "ok": True,
            })
        except Exception as fdr_err:
            try:
                result = _fetch_kr_pykrx(code, date)
                rows.append({
                    "name": display, "ticker": code,
                    "price": result["price"], "change_pct": result["change_pct"],
                    "week52_high": None, "week52_low": None,
                    "ok": True,
                })
            except Exception:
                rows.append({
                    "name": display, "ticker": code,
                    "price": None, "change_pct": None,
                    "week52_high": None, "week52_low": None,
                    "ok": False, "err": str(fdr_err),
                })
    return rows


def print_results(us: list, kr: list, fx: dict, indices: list):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    W = 72
    print(f"\n{'━' * W}")
    print(f"  포트폴리오 종가   ({now})")
    print(f"{'━' * W}")

    # 환율
    if fx.get("ok"):
        arrow = "▲" if (fx["change_pct"] or 0) >= 0 else "▼"
        print(f"\n  💱 USD/KRW: {fx['rate']:,.2f}원  {arrow}{abs(fx['change_pct'] or 0):.2f}%")

    # 주요 지수
    print(f"\n  ▶ 주요 지수")
    print(f"  {'─' * 50}")
    for idx in indices:
        if idx["ok"]:
            pct_val = idx["change_pct"] or 0
            arrow = "▲" if pct_val >= 0 else "▼"
            print(f"  {idx['name']:<10}  {idx['price']:>12,.2f}  {arrow}{abs(pct_val):.2f}%")

    # 미국 주식
    print(f"\n  ▶ 미국 주식 (USD)")
    print(f"  {'─' * 68}")
    print(f"  {'종목명':<22} {'티커':<6}  {'현재가':>14}  {'등락률':>8}  {'52주위치':>8}")
    print(f"  {'─' * 68}")
    for r in us:
        if r["ok"]:
            pct_val = r["change_pct"] or 0
            arrow = "▲" if pct_val >= 0 else "▼"
            pct = f"{arrow}{abs(pct_val):.2f}%"
            pos = _week52_pos(r["price"], r.get("week52_low"), r.get("week52_high"))
            pos_str = f"{pos}%" if pos is not None else " N/A"
            print(f"  {r['name']:<22} {r['ticker']:<6}  ${r['price']:>13,.2f}  {pct:>8}  {pos_str:>8}")
        else:
            print(f"  {r['name']:<22} {r['ticker']:<6}  {'조회 실패':>14}")

    # 국내 ETF
    print(f"\n  ▶ 국내 ETF (KRW)")
    print(f"  {'─' * 68}")
    print(f"  {'종목명':<32} {'코드':<7} {'현재가':>11}  {'등락률':>8}  {'52주위치':>8}")
    print(f"  {'─' * 68}")
    for r in kr:
        ticker = r.get("ticker") or "N/A"
        if r["ok"]:
            pct_val = r["change_pct"] or 0
            arrow = "▲" if pct_val >= 0 else "▼"
            pct = f"{arrow}{abs(pct_val):.2f}%"
            pos = _week52_pos(r["price"], r.get("week52_low"), r.get("week52_high"))
            pos_str = f"{pos}%" if pos is not None else " N/A"
            print(f"  {r['name']:<32} {ticker:<7} {r['price']:>10,}원  {pct:>8}  {pos_str:>8}")
        else:
            err = r.get("err", "오류")
            print(f"  {r['name']:<32} {ticker:<7} {err:>11}")

    print(f"\n{'━' * W}\n")


def _week52_pos(price, w52_low, w52_high) -> int | None:
    """52주 범위에서 현재가 위치 (0~100%)"""
    if not all([price, w52_low, w52_high]) or w52_high <= w52_low:
        return None
    return round((price - w52_low) / (w52_high - w52_low) * 100)


def save_prices(us: list, kr: list, fx: dict, indices: list):
    """data/prices.json 저장"""
    DATA_DIR.mkdir(exist_ok=True)
    data = {
        "fetched_at": datetime.now().isoformat(timespec="seconds"),
        "date": datetime.now().strftime("%Y-%m-%d"),
        "fx": fx,
        "indices": indices,
        "us": us,
        "kr": kr,
    }
    path = DATA_DIR / "prices.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  → 저장 완료: {path}")


def main():
    print("환율 조회 중...", flush=True)
    fx = fetch_fx()

    print("주요 지수 조회 중...", flush=True)
    indices = fetch_indices()

    print("미국 주식 조회 중...", flush=True)
    us = fetch_us()

    print("국내 ETF 조회 중...", flush=True)
    kr = fetch_kr()

    print_results(us, kr, fx, indices)
    save_prices(us, kr, fx, indices)


if __name__ == "__main__":
    main()
