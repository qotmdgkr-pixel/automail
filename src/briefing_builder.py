#!/usr/bin/env python3
"""브리핑 생성 — prices.json + news.json → HTML 이메일 + 카카오 텍스트
출력: data/briefing_email.html, data/briefing_kakao.txt
"""

import json
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"

CIRCLE_NUMS = ["①", "②", "③"]


# ── 데이터 로드 ───────────────────────────────────────────────────────────────

def load_data() -> tuple:
    prices = json.loads((DATA_DIR / "prices.json").read_text(encoding="utf-8"))
    news   = json.loads((DATA_DIR / "news.json").read_text(encoding="utf-8"))
    return prices, news


# ── 공통 헬퍼 ────────────────────────────────────────────────────────────────

def _pct_str(val) -> str:
    if val is None:
        return "N/A"
    arrow = "▲" if val >= 0 else "▼"
    return f"{arrow}{val:+.2f}%"   # val 자체가 부호를 포함


def _pct_color(val) -> str:
    if val is None or val == 0:
        return "#374151"
    return "#16a34a" if val >= 0 else "#dc2626"


# ── HTML 빌더 ────────────────────────────────────────────────────────────────

def _html_price_table_us(rows: list) -> str:
    head = """
    <table style="width:100%;border-collapse:collapse;font-size:14px;">
      <thead>
        <tr style="background:#1e3a5f;color:#fff;">
          <th style="padding:8px 12px;text-align:left;">종목명</th>
          <th style="padding:8px 12px;text-align:center;">티커</th>
          <th style="padding:8px 12px;text-align:right;">현재가 (USD)</th>
          <th style="padding:8px 12px;text-align:right;">등락률</th>
        </tr>
      </thead>
      <tbody>"""
    body = ""
    for i, r in enumerate(rows):
        bg = "#f8fafc" if i % 2 == 0 else "#ffffff"
        price = f"${r['price']:,.2f}" if r.get("price") else "—"
        pct   = _pct_str(r.get("change_pct"))
        color = _pct_color(r.get("change_pct"))
        body += f"""
        <tr style="background:{bg};">
          <td style="padding:8px 12px;">{r['name']}</td>
          <td style="padding:8px 12px;text-align:center;font-family:monospace;">{r['ticker']}</td>
          <td style="padding:8px 12px;text-align:right;font-weight:600;">{price}</td>
          <td style="padding:8px 12px;text-align:right;color:{color};font-weight:600;">{pct}</td>
        </tr>"""
    return head + body + "\n      </tbody>\n    </table>"


def _html_price_table_kr(rows: list) -> str:
    head = """
    <table style="width:100%;border-collapse:collapse;font-size:14px;">
      <thead>
        <tr style="background:#1e3a5f;color:#fff;">
          <th style="padding:8px 12px;text-align:left;">종목명</th>
          <th style="padding:8px 12px;text-align:center;">코드</th>
          <th style="padding:8px 12px;text-align:right;">현재가 (KRW)</th>
          <th style="padding:8px 12px;text-align:right;">등락률</th>
        </tr>
      </thead>
      <tbody>"""
    body = ""
    for i, r in enumerate(rows):
        bg = "#f8fafc" if i % 2 == 0 else "#ffffff"
        price = f"{r['price']:,}원" if r.get("price") else "—"
        pct   = _pct_str(r.get("change_pct"))
        color = _pct_color(r.get("change_pct"))
        body += f"""
        <tr style="background:{bg};">
          <td style="padding:8px 12px;">{r['name']}</td>
          <td style="padding:8px 12px;text-align:center;font-family:monospace;">{r['ticker']}</td>
          <td style="padding:8px 12px;text-align:right;font-weight:600;">{price}</td>
          <td style="padding:8px 12px;text-align:right;color:{color};font-weight:600;">{pct}</td>
        </tr>"""
    return head + body + "\n      </tbody>\n    </table>"


def _html_news_section(news_items: dict, price_us: list, price_kr: list) -> str:
    # 종목 순서: 미국 주식 → 국내 ETF (prices 순서 따름)
    order = [r["ticker"] for r in price_us] + [r["ticker"] for r in price_kr]
    html = ""
    for key in order:
        item = news_items.get(key)
        if not item:
            continue
        name = item.get("name", key)
        domestic = item.get("domestic", [])
        intl     = item.get("international", [])
        if not domestic and not intl:
            continue

        html += f"""
    <div style="margin-bottom:20px;">
      <h4 style="margin:0 0 6px;color:#1e3a5f;font-size:14px;border-left:3px solid #3b82f6;padding-left:8px;">
        ▶ {name}
      </h4>"""

        if domestic:
            html += '\n      <p style="margin:4px 0 2px;font-size:12px;color:#6b7280;font-weight:600;">🇰🇷 국내 뉴스</p>\n      <ul style="margin:0;padding-left:18px;">'
            for art in domestic[:3]:
                title = art.get("title", "")
                url   = art.get("url", "#")
                src   = art.get("source", "")
                pub   = art.get("published", "")
                html += (f'\n        <li style="margin:3px 0;font-size:13px;">'
                         f'<a href="{url}" style="color:#1d4ed8;text-decoration:none;">{title}</a>'
                         f'<span style="color:#9ca3af;font-size:11px;"> — {src} ({pub})</span></li>')
            html += "\n      </ul>"
        else:
            html += '\n      <p style="font-size:12px;color:#9ca3af;margin:2px 0;">국내 관련 뉴스 없음</p>'

        if intl:
            html += '\n      <p style="margin:8px 0 2px;font-size:12px;color:#6b7280;font-weight:600;">🌐 해외 뉴스 (번역)</p>\n      <ul style="margin:0;padding-left:18px;">'
            for art in intl[:3]:
                title_kr  = art.get("title", "")
                title_org = art.get("title_original", "")
                url       = art.get("url", "#")
                src       = art.get("source", "")
                pub       = art.get("published", "")
                html += (f'\n        <li style="margin:3px 0;font-size:13px;">'
                         f'<a href="{url}" style="color:#1d4ed8;text-decoration:none;">{title_kr}</a>'
                         f'<br><span style="color:#9ca3af;font-size:11px;">{title_org} — {src} ({pub})</span></li>')
            html += "\n      </ul>"
        else:
            html += '\n      <p style="font-size:12px;color:#9ca3af;margin:2px 0;">해외 관련 뉴스 없음</p>'

        html += "\n    </div>"
    return html


def build_email_html(prices: dict, news: dict) -> str:
    date    = prices.get("date", datetime.now().strftime("%Y-%m-%d"))
    us_rows = prices.get("us", [])
    kr_rows = prices.get("kr", [])
    news_items = news.get("items", {})

    table_us = _html_price_table_us(us_rows)
    table_kr = _html_price_table_kr(kr_rows)
    news_html = _html_news_section(news_items, us_rows, kr_rows)

    # 뉴스 있는 종목 수 카운트
    has_news = sum(
        1 for v in news_items.values()
        if v.get("domestic") or v.get("international")
    )

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>포트폴리오 브리핑 {date}</title>
</head>
<body style="margin:0;padding:0;background:#f1f5f9;font-family:'Apple SD Gothic Neo',Arial,sans-serif;">

<div style="max-width:680px;margin:24px auto;background:#ffffff;border-radius:12px;
            box-shadow:0 2px 8px rgba(0,0,0,.08);overflow:hidden;">

  <!-- 헤더 -->
  <div style="background:linear-gradient(135deg,#1e3a5f,#2563eb);padding:24px 28px;color:#fff;">
    <div style="font-size:22px;font-weight:700;">📊 포트폴리오 브리핑</div>
    <div style="font-size:14px;opacity:.85;margin-top:4px;">{date} · 자동 생성</div>
  </div>

  <!-- 본문 -->
  <div style="padding:24px 28px;">

    <!-- 섹션 1: 미국 주식 -->
    <h3 style="margin:0 0 12px;font-size:16px;color:#1e3a5f;">
      📈 미국 주식 종가 (USD)
    </h3>
    {table_us}

    <!-- 섹션 2: 국내 ETF -->
    <h3 style="margin:28px 0 12px;font-size:16px;color:#1e3a5f;">
      🇰🇷 국내 ETF 종가 (KRW)
    </h3>
    {table_kr}

    <!-- 섹션 3: 뉴스 -->
    <h3 style="margin:28px 0 16px;font-size:16px;color:#1e3a5f;">
      📰 오늘의 주요 뉴스 ({has_news}종목)
    </h3>
    {news_html}

  </div><!-- /본문 -->

  <!-- 푸터 -->
  <div style="background:#f8fafc;padding:14px 28px;border-top:1px solid #e2e8f0;
              font-size:11px;color:#94a3b8;text-align:center;">
    기준일: {date} | 가격: yfinance(미국) · FinanceDataReader(국내) | 뉴스: Google News RSS
  </div>

</div><!-- /wrapper -->
</body>
</html>"""


# ── 카카오 텍스트 빌더 ────────────────────────────────────────────────────────

def _kakao_price_us(rows: list) -> str:
    lines = []
    for r in rows:
        price = f"${r['price']:,.2f}" if r.get("price") else "—"
        pct   = _pct_str(r.get("change_pct"))
        lines.append(f"{r['name']}({r['ticker']})  {price}  {pct}")
    return "\n".join(lines)


def _kakao_price_kr(rows: list) -> str:
    lines = []
    for r in rows:
        price = f"{r['price']:,}원" if r.get("price") else "—"
        pct   = _pct_str(r.get("change_pct"))
        lines.append(f"{r['name']}  {price}  {pct}")
    return "\n".join(lines)


def build_kakao_text(prices: dict, news: dict) -> str:
    """전체 내용 생성 — 글자 수 제한 없음 (kakao_sender에서 분할 발송)"""
    date       = prices.get("date", datetime.now().strftime("%Y-%m-%d"))
    us_rows    = prices.get("us", [])
    kr_rows    = prices.get("kr", [])
    news_items = news.get("items", {})
    div        = "━" * 20

    header = f"📊 포트폴리오 브리핑 | {date}\n{div}"
    us_sec = f"\n📈 미국 주식 (USD)\n{_kakao_price_us(us_rows)}"
    kr_sec = f"\n\n🇰🇷 국내 ETF (KRW)\n{_kakao_price_kr(kr_rows)}"
    footer = f"\n\n{div}\n자동생성 | {date}"

    news_lines = ["\n\n📰 주요 뉴스"]
    order = [r["ticker"] for r in us_rows] + [r["ticker"] for r in kr_rows]
    for key in order:
        item = news_items.get(key)
        if not item:
            continue
        dom  = item.get("domestic",      [])
        intl = item.get("international", [])
        if not dom and not intl:
            continue
        news_lines.append(f"\n▶ {item.get('name', key)}")
        for i, a in enumerate(dom[:3]):
            t = a["title"][:50] + "…" if len(a["title"]) > 50 else a["title"]
            news_lines.append(f" [국]{CIRCLE_NUMS[i]} {t}")
        for i, a in enumerate(intl[:3]):
            t = a["title"][:50] + "…" if len(a["title"]) > 50 else a["title"]
            news_lines.append(f" [해]{CIRCLE_NUMS[i]} {t}")

    news_sec = "\n".join(news_lines)
    return header + us_sec + kr_sec + news_sec + footer


# ── 저장 & 메인 ──────────────────────────────────────────────────────────────

def save_briefings(html: str, text: str):
    DATA_DIR.mkdir(exist_ok=True)
    html_path = DATA_DIR / "briefing_email.html"
    txt_path  = DATA_DIR / "briefing_kakao.txt"
    html_path.write_text(html, encoding="utf-8")
    txt_path.write_text(text, encoding="utf-8")
    print(f"  이메일 HTML → {html_path}")
    print(f"  카카오 텍스트 → {txt_path}")


def main():
    import sys, io
    # Windows 터미널 UTF-8 출력 강제
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    prices, news = load_data()
    html = build_email_html(prices, news)
    text = build_kakao_text(prices, news)
    save_briefings(html, text)

    print(f"\n{'─'*50}")
    print("[ 카카오톡 브리핑 미리보기 ]")
    print(f"{'─'*50}")
    print(text)
    print(f"{'─'*50}")
    chunks = (len(text) + 1899) // 1900
    print(f"글자 수: {len(text)}자 → {chunks}개 메시지로 분할 발송")


if __name__ == "__main__":
    main()
