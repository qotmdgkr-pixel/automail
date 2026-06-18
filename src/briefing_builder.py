#!/usr/bin/env python3
"""브리핑 생성 — prices.json + news.json + economic_calendar.json → HTML 이메일 + 카카오 텍스트
출력: data/briefing_email.html, data/briefing_kakao.txt
"""

import json
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"

CIRCLE_NUMS = ["①", "②", "③"]


# ── 데이터 로드 ───────────────────────────────────────────────────────────────

def load_data() -> tuple:
    prices   = json.loads((DATA_DIR / "prices.json").read_text(encoding="utf-8"))
    news     = json.loads((DATA_DIR / "news.json").read_text(encoding="utf-8"))
    cal_path = DATA_DIR / "economic_calendar.json"
    calendar = json.loads(cal_path.read_text(encoding="utf-8")) if cal_path.exists() else {}
    return prices, news, calendar


# ── 공통 헬퍼 ────────────────────────────────────────────────────────────────

def _pct_str(val) -> str:
    if val is None:
        return "N/A"
    arrow = "▲" if val >= 0 else "▼"
    return f"{arrow}{val:+.2f}%"


def _pct_color(val) -> str:
    if val is None or val == 0:
        return "#374151"
    return "#16a34a" if val >= 0 else "#dc2626"


def _week52_pos(price, w52_low, w52_high):
    """52주 범위 내 현재가 위치 (0~100, None if unavailable)"""
    if not all([price, w52_low, w52_high]) or w52_high <= w52_low:
        return None
    return round((price - w52_low) / (w52_high - w52_low) * 100)


# ── HTML 빌더 ────────────────────────────────────────────────────────────────

def _html_section_header(title: str) -> str:
    return f'<h3 style="margin:28px 0 12px;font-size:16px;color:#1e3a5f;">{title}</h3>'


def _fg_color(score) -> str:
    if score is None:
        return "#6b7280"
    if score <= 25:  return "#dc2626"
    if score <= 45:  return "#f97316"
    if score <= 55:  return "#6b7280"
    if score <= 75:  return "#16a34a"
    return "#065f46"


def _html_fx_indices(fx: dict, indices: list, us10y: dict, fear_greed: dict) -> str:
    """환율 + 10Y금리 + 공포탐욕 + 주요 지수 섹션 HTML"""
    html = ""

    # 환율 / 10Y / 공포탐욕 — 한 줄 카드 묶음
    cards = []
    if fx.get("ok") and fx.get("rate"):
        pct   = _pct_str(fx.get("change_pct"))
        color = _pct_color(fx.get("change_pct"))
        cards.append(
            f'<div style="flex:1;background:#f8fafc;border-radius:8px;padding:10px 14px;">'
            f'<div style="font-size:11px;color:#6b7280;margin-bottom:4px;">💱 USD/KRW</div>'
            f'<div style="font-size:16px;font-weight:700;">{fx["rate"]:,.2f}원</div>'
            f'<div style="font-size:12px;color:{color};font-weight:600;">{pct}</div></div>'
        )
    if us10y.get("ok") and us10y.get("rate") is not None:
        bp    = us10y.get("change_bp") or 0
        arrow = "▲" if bp >= 0 else "▼"
        color = "#dc2626" if bp > 0 else "#16a34a" if bp < 0 else "#374151"
        cards.append(
            f'<div style="flex:1;background:#f8fafc;border-radius:8px;padding:10px 14px;">'
            f'<div style="font-size:11px;color:#6b7280;margin-bottom:4px;">🏦 미국 10Y 금리</div>'
            f'<div style="font-size:16px;font-weight:700;">{us10y["rate"]:.3f}%</div>'
            f'<div style="font-size:12px;color:{color};font-weight:600;">{arrow}{abs(bp)}bp</div></div>'
        )
    if fear_greed.get("ok") and fear_greed.get("score") is not None:
        score = fear_greed["score"]
        color = _fg_color(score)
        label = fear_greed.get("rating_kr", "")
        cards.append(
            f'<div style="flex:1;background:#f8fafc;border-radius:8px;padding:10px 14px;">'
            f'<div style="font-size:11px;color:#6b7280;margin-bottom:4px;">😨 공포탐욕 지수</div>'
            f'<div style="font-size:16px;font-weight:700;color:{color};">{score:.0f}</div>'
            f'<div style="font-size:12px;color:{color};font-weight:600;">{label}</div></div>'
        )
    if cards:
        html += f'\n    <div style="display:flex;gap:10px;margin-bottom:16px;">{"".join(cards)}</div>'

    # 주요 지수 테이블
    if indices:
        html += """
    <table style="width:100%;border-collapse:collapse;font-size:13px;margin-bottom:8px;">
      <thead>
        <tr style="background:#f1f5f9;">
          <th style="padding:6px 10px;text-align:left;color:#6b7280;">지수</th>
          <th style="padding:6px 10px;text-align:right;color:#6b7280;">현재가</th>
          <th style="padding:6px 10px;text-align:right;color:#6b7280;">등락률</th>
        </tr>
      </thead>
      <tbody>"""
        for idx in indices:
            if not idx.get("ok"):
                continue
            pct   = _pct_str(idx.get("change_pct"))
            color = _pct_color(idx.get("change_pct"))
            html += f"""
        <tr>
          <td style="padding:5px 10px;font-weight:600;">{idx['name']}</td>
          <td style="padding:5px 10px;text-align:right;">{idx['price']:,.2f}</td>
          <td style="padding:5px 10px;text-align:right;color:{color};font-weight:600;">{pct}</td>
        </tr>"""
        html += "\n      </tbody>\n    </table>"

    return html


def _html_week52_bar(price, w52_low, w52_high) -> str:
    """52주 범위 미니 프로그레스 바 HTML"""
    pos = _week52_pos(price, w52_low, w52_high)
    if pos is None:
        return '<span style="color:#9ca3af;font-size:11px;">N/A</span>'
    bar_color = "#16a34a" if pos >= 50 else "#f59e0b" if pos >= 25 else "#dc2626"
    low_fmt  = f"{w52_low:,}"  if isinstance(w52_low,  int) else f"{w52_low:,.2f}"
    high_fmt = f"{w52_high:,}" if isinstance(w52_high, int) else f"{w52_high:,.2f}"
    return (f'<div style="font-size:10px;color:#6b7280;">'
            f'<div style="background:#e5e7eb;border-radius:3px;height:5px;width:80px;margin-bottom:2px;">'
            f'<div style="background:{bar_color};height:5px;border-radius:3px;width:{pos}%;"></div></div>'
            f'{pos}% ({low_fmt}~{high_fmt})</div>')


def _html_price_table_us(rows: list) -> str:
    head = """
    <table style="width:100%;border-collapse:collapse;font-size:14px;">
      <thead>
        <tr style="background:#1e3a5f;color:#fff;">
          <th style="padding:8px 10px;text-align:left;">종목명</th>
          <th style="padding:8px 10px;text-align:center;">티커</th>
          <th style="padding:8px 10px;text-align:right;">현재가 (USD)</th>
          <th style="padding:8px 10px;text-align:right;">등락률</th>
          <th style="padding:8px 10px;text-align:center;">52주 범위</th>
        </tr>
      </thead>
      <tbody>"""
    body = ""
    for i, r in enumerate(rows):
        bg    = "#f8fafc" if i % 2 == 0 else "#ffffff"
        price = f"${r['price']:,.2f}" if r.get("price") else "—"
        pct   = _pct_str(r.get("change_pct"))
        color = _pct_color(r.get("change_pct"))
        w52   = _html_week52_bar(r.get("price"), r.get("week52_low"), r.get("week52_high"))
        body += f"""
        <tr style="background:{bg};">
          <td style="padding:8px 10px;">{r['name']}</td>
          <td style="padding:8px 10px;text-align:center;font-family:monospace;">{r['ticker']}</td>
          <td style="padding:8px 10px;text-align:right;font-weight:600;">{price}</td>
          <td style="padding:8px 10px;text-align:right;color:{color};font-weight:600;">{pct}</td>
          <td style="padding:8px 10px;text-align:center;">{w52}</td>
        </tr>"""
    return head + body + "\n      </tbody>\n    </table>"


def _html_price_table_kr(rows: list) -> str:
    head = """
    <table style="width:100%;border-collapse:collapse;font-size:14px;">
      <thead>
        <tr style="background:#1e3a5f;color:#fff;">
          <th style="padding:8px 10px;text-align:left;">종목명</th>
          <th style="padding:8px 10px;text-align:center;">코드</th>
          <th style="padding:8px 10px;text-align:right;">현재가 (KRW)</th>
          <th style="padding:8px 10px;text-align:right;">등락률</th>
          <th style="padding:8px 10px;text-align:center;">52주 범위</th>
        </tr>
      </thead>
      <tbody>"""
    body = ""
    for i, r in enumerate(rows):
        bg    = "#f8fafc" if i % 2 == 0 else "#ffffff"
        price = f"{r['price']:,}원" if r.get("price") else "—"
        pct   = _pct_str(r.get("change_pct"))
        color = _pct_color(r.get("change_pct"))
        w52   = _html_week52_bar(r.get("price"), r.get("week52_low"), r.get("week52_high"))
        body += f"""
        <tr style="background:{bg};">
          <td style="padding:8px 10px;">{r['name']}</td>
          <td style="padding:8px 10px;text-align:center;font-family:monospace;">{r['ticker']}</td>
          <td style="padding:8px 10px;text-align:right;font-weight:600;">{price}</td>
          <td style="padding:8px 10px;text-align:right;color:{color};font-weight:600;">{pct}</td>
          <td style="padding:8px 10px;text-align:center;">{w52}</td>
        </tr>"""
    return head + body + "\n      </tbody>\n    </table>"


def _html_economic_calendar(calendar: dict) -> str:
    """경제 지표 발표 일정 HTML"""
    today_events = calendar.get("today", [])
    week_events  = calendar.get("this_week", [])
    events       = today_events if today_events else week_events
    label        = "오늘" if today_events else "이번 주"

    if not events:
        return '<p style="color:#9ca3af;font-size:13px;margin:4px 0;">예정된 주요 경제 지표 없음</p>'

    impact_color = {"High": "#dc2626", "Medium": "#f59e0b"}
    impact_label = {"High": "HIGH", "Medium": "MED"}

    html = f'<p style="font-size:12px;color:#6b7280;margin:0 0 6px;">{label} 발표 기준</p>'
    html += """
    <table style="width:100%;border-collapse:collapse;font-size:13px;">
      <thead>
        <tr style="background:#f1f5f9;">
          <th style="padding:5px 8px;text-align:left;color:#6b7280;">영향</th>
          <th style="padding:5px 8px;text-align:left;color:#6b7280;">지표명</th>
          <th style="padding:5px 8px;text-align:center;color:#6b7280;">통화</th>
          <th style="padding:5px 8px;text-align:center;color:#6b7280;">시간(ET)</th>
          <th style="padding:5px 8px;text-align:right;color:#6b7280;">예상</th>
          <th style="padding:5px 8px;text-align:right;color:#6b7280;">이전</th>
        </tr>
      </thead>
      <tbody>"""
    for ev in events:
        impact = ev.get("impact", "")
        color  = impact_color.get(impact, "#6b7280")
        badge  = impact_label.get(impact, impact)
        html += f"""
        <tr style="border-bottom:1px solid #f1f5f9;">
          <td style="padding:5px 8px;">
            <span style="background:{color};color:#fff;font-size:10px;
                         font-weight:700;padding:2px 5px;border-radius:3px;">{badge}</span>
          </td>
          <td style="padding:5px 8px;font-weight:500;">{ev.get('title','')}</td>
          <td style="padding:5px 8px;text-align:center;color:#6b7280;">{ev.get('country','')}</td>
          <td style="padding:5px 8px;text-align:center;color:#6b7280;">{ev.get('time','')}</td>
          <td style="padding:5px 8px;text-align:right;">{ev.get('forecast','—') or '—'}</td>
          <td style="padding:5px 8px;text-align:right;color:#9ca3af;">{ev.get('previous','—') or '—'}</td>
        </tr>"""
    html += "\n      </tbody>\n    </table>"
    return html


def _html_news_section(news_items: dict, price_us: list, price_kr: list) -> str:
    order = [r["ticker"] for r in price_us] + [r["ticker"] for r in price_kr]
    html = ""
    for key in order:
        item = news_items.get(key)
        if not item:
            continue
        name     = item.get("name", key)
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


def build_email_html(prices: dict, news: dict, calendar: dict) -> str:
    date       = prices.get("date", datetime.now().strftime("%Y-%m-%d"))
    us_rows    = prices.get("us", [])
    kr_rows    = prices.get("kr", [])
    fx         = prices.get("fx", {})
    us10y      = prices.get("us10y", {})
    fear_greed = prices.get("fear_greed", {})
    indices    = prices.get("indices", [])
    news_items = news.get("items", {})

    fx_idx_html = _html_fx_indices(fx, indices, us10y, fear_greed)
    table_us    = _html_price_table_us(us_rows)
    table_kr    = _html_price_table_kr(kr_rows)
    cal_html    = _html_economic_calendar(calendar)
    news_html   = _html_news_section(news_items, us_rows, kr_rows)

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

    {_html_section_header("💱 환율 &amp; 주요 지수")}
    {fx_idx_html}

    {_html_section_header("📈 미국 주식 종가 (USD)")}
    {table_us}

    {_html_section_header("🇰🇷 국내 ETF 종가 (KRW)")}
    {table_kr}

    {_html_section_header("📅 경제 지표 발표 일정")}
    {cal_html}

    {_html_section_header(f"📰 오늘의 주요 뉴스 ({has_news}종목)")}
    {news_html}

  </div><!-- /본문 -->

  <!-- 푸터 -->
  <div style="background:#f8fafc;padding:14px 28px;border-top:1px solid #e2e8f0;
              font-size:11px;color:#94a3b8;text-align:center;">
    기준일: {date} | 가격: yfinance · FinanceDataReader | 뉴스: Google News RSS | 캘린더: Forex Factory
  </div>

</div><!-- /wrapper -->
</body>
</html>"""


# ── 카카오 텍스트 빌더 ────────────────────────────────────────────────────────

def _kakao_pct(val) -> str:
    if val is None:
        return "N/A"
    arrow = "▲" if val >= 0 else "▼"
    return f"{arrow}{abs(val):.2f}%"


def _kakao_w52(price, w52_low, w52_high) -> str:
    pos = _week52_pos(price, w52_low, w52_high)
    return f" [52w:{pos}%]" if pos is not None else ""


def _kakao_fx_indices(fx: dict, indices: list, us10y: dict, fear_greed: dict) -> str:
    lines = []
    if fx.get("ok") and fx.get("rate"):
        lines.append(f"💱 USD/KRW  {fx['rate']:,.2f}원  {_kakao_pct(fx.get('change_pct'))}")
    if us10y.get("ok") and us10y.get("rate") is not None:
        bp    = us10y.get("change_bp") or 0
        arrow = "▲" if bp >= 0 else "▼"
        lines.append(f"🏦 미국 10Y  {us10y['rate']:.3f}%  {arrow}{abs(bp)}bp")
    if fear_greed.get("ok") and fear_greed.get("score") is not None:
        lines.append(f"😨 공포탐욕  {fear_greed['score']:.0f}  ({fear_greed.get('rating_kr','')})")
    if indices:
        lines.append("📊 주요 지수")
        for idx in indices:
            if not idx.get("ok"):
                continue
            lines.append(f"  {idx['name']:<10} {idx['price']:>12,.2f}  {_kakao_pct(idx.get('change_pct'))}")
    return "\n".join(lines)


def _kakao_price_us(rows: list) -> str:
    lines = []
    for r in rows:
        price = f"${r['price']:,.2f}" if r.get("price") else "—"
        pct   = _kakao_pct(r.get("change_pct"))
        w52   = _kakao_w52(r.get("price"), r.get("week52_low"), r.get("week52_high"))
        lines.append(f"{r['name']}({r['ticker']})  {price}  {pct}{w52}")
    return "\n".join(lines)


def _kakao_price_kr(rows: list) -> str:
    lines = []
    for r in rows:
        price = f"{r['price']:,}원" if r.get("price") else "—"
        pct   = _kakao_pct(r.get("change_pct"))
        w52   = _kakao_w52(r.get("price"), r.get("week52_low"), r.get("week52_high"))
        lines.append(f"{r['name']}  {price}  {pct}{w52}")
    return "\n".join(lines)


def _kakao_economic_calendar(calendar: dict) -> str:
    today_events = calendar.get("today", [])
    week_events  = calendar.get("this_week", [])
    events       = today_events if today_events else week_events
    if not events:
        return "예정된 주요 경제 지표 없음"

    label = "오늘" if today_events else "이번 주"
    impact_label = {"High": "★HIGH", "Medium": "☆MED"}

    lines = [f"({label} 기준)"]
    for ev in events[:8]:
        badge  = impact_label.get(ev.get("impact", ""), ev.get("impact", ""))
        title  = ev.get("title", "")
        cntry  = ev.get("country", "")
        time_  = ev.get("time", "")
        fcst   = ev.get("forecast", "")
        prev   = ev.get("previous", "")
        detail = (f" 예:{fcst}" if fcst else "") + (f" 전:{prev}" if prev else "")
        lines.append(f" {badge} {title} ({cntry}) {time_}{detail}")

    return "\n".join(lines)


def build_kakao_text(prices: dict, news: dict, calendar: dict) -> str:
    """전체 내용 생성 — 글자 수 제한 없음 (kakao_sender에서 분할 발송)"""
    date       = prices.get("date", datetime.now().strftime("%Y-%m-%d"))
    us_rows    = prices.get("us", [])
    kr_rows    = prices.get("kr", [])
    fx         = prices.get("fx", {})
    us10y      = prices.get("us10y", {})
    fear_greed = prices.get("fear_greed", {})
    indices    = prices.get("indices", [])
    news_items = news.get("items", {})
    div        = "━" * 20

    header  = f"📊 포트폴리오 브리핑 | {date}\n{div}"
    fx_sec  = f"\n{_kakao_fx_indices(fx, indices, us10y, fear_greed)}" if (fx.get("ok") or indices) else ""
    us_sec  = f"\n\n📈 미국 주식 (USD)\n{_kakao_price_us(us_rows)}"
    kr_sec  = f"\n\n🇰🇷 국내 ETF (KRW)\n{_kakao_price_kr(kr_rows)}"
    cal_sec = f"\n\n📅 경제 지표 발표\n{_kakao_economic_calendar(calendar)}"
    footer  = f"\n\n{div}\n자동생성 | {date}"

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
    return header + fx_sec + us_sec + kr_sec + cal_sec + news_sec + footer


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
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    prices, news, calendar = load_data()
    html = build_email_html(prices, news, calendar)
    text = build_kakao_text(prices, news, calendar)
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
