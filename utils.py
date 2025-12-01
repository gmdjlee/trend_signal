"""유틸리티: 종목 조회, 공통 헬퍼."""

from functools import lru_cache

import pandas as pd

from pykrx import stock


@lru_cache(maxsize=1)
def get_stock_list() -> pd.DataFrame:
    """전체 종목 리스트 조회 (캐시)."""
    from datetime import datetime, timedelta

    # 최근 영업일 추정 (주말 회피)
    dt = datetime.now()
    for _ in range(7):
        date_str = dt.strftime("%Y%m%d")
        try:
            codes = stock.get_market_ticker_list(date_str, market="ALL")
            if codes:
                break
        except Exception:
            pass
        dt -= timedelta(days=1)
    else:
        codes = []

    names = [stock.get_market_ticker_name(c) for c in codes]
    return pd.DataFrame({"code": codes, "name": names})


def to_code(query: str) -> str | None:
    """종목명 또는 코드 → 6자리 코드 변환.

    Args:
        query: 종목명(예: '삼성전자') 또는 코드(예: '005930')

    Returns:
        6자리 종목코드 또는 None (미발견 시)
    """
    q = query.strip()

    # 6자리 숫자면 코드로 간주
    if q.isdigit() and len(q) == 6:
        return q

    df = get_stock_list()

    if df.empty:
        return None

    # 코드 매칭
    if q in df["code"].values:
        return q

    # 종목명 정확 매칭
    match = df[df["name"] == q]
    if not match.empty:
        return match.iloc[0]["code"]

    # 부분 매칭 (첫 번째 결과)
    try:
        match = df[df["name"].str.contains(q, na=False)]
        if not match.empty:
            return match.iloc[0]["code"]
    except Exception:
        pass

    return None


def to_name(code: str) -> str:
    """종목코드 → 종목명."""
    return stock.get_market_ticker_name(code) or code


def resample_weekly(df: pd.DataFrame) -> pd.DataFrame:
    """일봉 → 주봉 변환 (금요일 기준).

    Args:
        df: OHLCV 컬럼을 가진 일봉 DataFrame

    Returns:
        주봉 DataFrame
    """
    r = df.resample("W-FRI")
    return pd.DataFrame(
        {
            "Open": r["Open"].first(),
            "High": r["High"].max(),
            "Low": r["Low"].min(),
            "Close": r["Close"].last(),
            "Volume": r["Volume"].sum(),
        }
    ).dropna()


def resample_monthly(df: pd.DataFrame) -> pd.DataFrame:
    """일봉 → 월봉 변환 (월말 기준).

    Args:
        df: OHLCV 컬럼을 가진 일봉 DataFrame

    Returns:
        월봉 DataFrame
    """
    r = df.resample("M")
    return pd.DataFrame(
        {
            "Open": r["Open"].first(),
            "High": r["High"].max(),
            "Low": r["Low"].min(),
            "Close": r["Close"].last(),
            "Volume": r["Volume"].sum(),
        }
    ).dropna()


def filter_period(df: pd.DataFrame, years: int = 1) -> pd.DataFrame:
    """최근 N년 데이터만 필터링.

    Args:
        df: DatetimeIndex를 가진 DataFrame
        years: 필터링할 연도 수

    Returns:
        필터링된 DataFrame
    """
    if df.empty:
        return df
    last_date = df.index.max()
    start_date = last_date - pd.DateOffset(years=years)
    return df[df.index >= start_date]
