"""price_fetcher 단위 테스트 — 실제 네트워크 호출 없이 구조만 검증"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config import KR_ETFS, US_STOCKS


def test_us_stocks_has_8_items():
    assert len(US_STOCKS) == 8, f"US_STOCKS는 8종목이어야 함, 현재: {len(US_STOCKS)}"


def test_kr_etfs_has_10_items():
    assert len(KR_ETFS) == 10, f"KR_ETFS는 10종목이어야 함, 현재: {len(KR_ETFS)}"


def test_kr_etfs_have_required_fields():
    required = {"display", "keyword", "code"}
    for etf in KR_ETFS:
        missing = required - etf.keys()
        assert not missing, f"{etf.get('display', '?')} 에 필드 누락: {missing}"


def test_us_stocks_tickers_are_strings():
    for name, ticker in US_STOCKS.items():
        assert isinstance(ticker, str) and ticker.isupper(), (
            f"{name} 티커 형식 오류: {ticker!r}"
        )


def test_kr_etfs_codes_are_6_digits():
    for etf in KR_ETFS:
        code = etf["code"]
        assert code.isdigit() and len(code) == 6, (
            f"{etf['display']} 코드 형식 오류: {code!r}"
        )


def test_fetch_us_result_structure(monkeypatch):
    """fetch_us() 반환값 구조 검증 (yfinance mock)"""
    import price_fetcher

    class FakeFastInfo:
        last_price = 195.32
        previous_close = 193.10

    class FakeTicker:
        fast_info = FakeFastInfo()

    monkeypatch.setattr(price_fetcher.yf, "Ticker", lambda sym: FakeTicker())

    rows = price_fetcher.fetch_us()
    assert len(rows) == 8, f"결과는 8개여야 함, 현재: {len(rows)}"

    required_keys = {"name", "ticker", "price", "change_pct", "ok"}
    for row in rows:
        missing = required_keys - row.keys()
        assert not missing, f"필드 누락: {missing} in {row}"
        assert row["ok"] is True
        assert isinstance(row["price"], float)
        assert isinstance(row["change_pct"], float)
