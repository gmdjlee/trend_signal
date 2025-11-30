"""데이터 수집: pykrx 기반 OHLCV 조회."""

from datetime import datetime, timedelta

import pandas as pd
from utils import resample_weekly, to_code

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
        period: 'daily' 또는 'weekly'
        adjusted: True=수정주가, False=일반주가

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

    # pykrx로 데이터 조회 (수정주가 옵션)
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

    # 주봉 변환
    if period == "weekly":
        df = resample_weekly(df)

    return df, code
