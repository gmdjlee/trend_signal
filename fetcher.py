"""데이터 수집: pykrx 기반 OHLCV 조회."""

from datetime import datetime, timedelta

import pandas as pd
from utils import resample_monthly, resample_weekly, to_code

from pykrx import stock


def fetch_ohlcv(
    query: str,
    start: str | None = None,
    end: str | None = None,
    period: str = "weekly",
    adjusted: bool = True,
) -> tuple[pd.DataFrame | None, str | None]:
    """종목 OHLCV 데이터 수집.

    Args:
        query: 종목명 또는 코드
        start: 시작일 (YYYYMMDD 또는 YYYY-MM-DD)
        end: 종료일
        period: 'daily', 'weekly', 'monthly'
        adjusted: True=수정주가(네이버), False=일반주가(KRX)

    Note:
        pykrx의 수정주가는 액면분할만 반영하며,
        yfinance와 달리 배당 재투자는 미반영됩니다.

    Returns:
        (DataFrame, 종목코드) 또는 (None, None)
    """
    code = to_code(query)
    if not code:
        print(f"[오류] '{query}' 종목을 찾을 수 없습니다.")
        return None, None

    # 날짜 기본값
    end_dt = datetime.now()
    start_dt = end_dt - timedelta(days=365 * 3)  # 기본 3년

    if start:
        start = start.replace("-", "")
    else:
        start = start_dt.strftime("%Y%m%d")

    if end:
        end = end.replace("-", "")
    else:
        end = end_dt.strftime("%Y%m%d")

    # pykrx로 데이터 조회
    df = stock.get_market_ohlcv_by_date(start, end, code, adjusted=adjusted)

    if df.empty:
        print(f"[오류] '{query}'({code}) 데이터 없음")
        return None, None

    # 컬럼명 정리
    col_map = {
        "시가": "Open",
        "고가": "High",
        "저가": "Low",
        "종가": "Close",
        "거래량": "Volume",
    }
    df = df.rename(columns=col_map)[["Open", "High", "Low", "Close", "Volume"]]

    # 유효 데이터 필터
    df = df[(df[["Open", "High", "Low", "Close"]] > 0).all(axis=1)]

    if df.empty:
        print(f"[오류] '{query}'({code}) 유효 데이터 없음")
        return None, None

    # 리샘플링
    if period == "weekly":
        df = resample_weekly(df)
    elif period == "monthly":
        df = resample_monthly(df)
    # period == "daily"면 그대로 반환

    return df, code


def fetch_multi_period(
    query: str, start: str | None = None, end: str | None = None, adjusted: bool = True
) -> dict | None:
    """일봉/주봉/월봉 데이터 동시 조회.

    Args:
        query: 종목명 또는 코드
        start: 시작일
        end: 종료일
        adjusted: 수정주가 여부

    Returns:
        {"daily": df, "weekly": df, "monthly": df, "code": str} 또는 None
    """
    daily, code = fetch_ohlcv(query, start, end, period="daily", adjusted=adjusted)
    if daily is None:
        return None

    weekly = resample_weekly(daily)
    monthly = resample_monthly(daily)

    return {"daily": daily, "weekly": weekly, "monthly": monthly, "code": code}
