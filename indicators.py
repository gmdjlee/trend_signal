"""기술적 지표: CMF, Fear & Greed, DeMark, Elder Impulse 등."""

import numpy as np
import pandas as pd


def calc_ma(s: pd.Series, n: int) -> pd.Series:
    """이동평균."""
    return s.rolling(n).mean()


def calc_ema(s: pd.Series, n: int) -> pd.Series:
    """지수이동평균."""
    return s.ewm(span=n, adjust=False).mean()


def calc_cmf(df: pd.DataFrame, n: int = 4) -> pd.Series:
    """Chaikin Money Flow.

    Args:
        df: OHLCV DataFrame
        n: 기간 (기본 4주)
    """
    rng = df["High"] - df["Low"]
    mf_mult = ((df["Close"] - df["Low"]) - (df["High"] - df["Close"])) / rng.replace(
        0, np.nan
    )
    mf_vol = mf_mult * df["Volume"]
    return mf_vol.rolling(n).sum() / df["Volume"].rolling(n).sum()


def calc_fear_greed(df: pd.DataFrame) -> pd.Series:
    """Fear & Greed 지수 계산.

    구성요소:
    - 모멘텀 (5주 로그 수익률)
    - 52주 포지션 (현재가 위치)
    - 거래량 급증
    - 변동성 스파이크
    """
    close = df["Close"]
    vol = df["Volume"]

    # 1) 모멘텀 (5주 로그 수익률)
    mom = (np.log(close) - np.log(close.shift(5))) * 100

    # 2) 52주 포지션
    low52 = close.rolling(52, min_periods=1).min()
    high52 = close.rolling(52, min_periods=1).max()
    pos52 = ((close - low52) / (high52 - low52)).clip(0, 1)

    # 3) 거래량 급증
    vol_r = vol.rolling(5, min_periods=1).mean()
    vol_p = vol.rolling(20, min_periods=1).mean()
    vol_surge = (vol_r / vol_p).clip(0, 3)

    # 4) 변동성 스파이크
    ret = close.pct_change()
    std_r = ret.rolling(5, min_periods=1).std()
    std_p = ret.rolling(20, min_periods=1).std()
    vol_spike = (std_r / std_p).clip(0, 3)

    # 스무딩 및 정규화
    m = (mom.rolling(7, min_periods=1).mean() / 10).clip(-1, 1.5)
    p = (2 * pos52.rolling(7, min_periods=1).mean() - 1).clip(-1, 1.5)
    v = (vol_surge.rolling(10, min_periods=1).mean() - 1).clip(-0.5, 1.2)
    vs = -(vol_spike.rolling(10, min_periods=1).mean() - 1).clip(-0.5, 1.2)

    # 가중 합산 (모멘텀/포지션 각 45%, 거래량 지표 각 5%)
    return 0.45 * m + 0.45 * p + 0.05 * v + 0.05 * vs


def calc_td_setup(df: pd.DataFrame, col: str = "Close") -> pd.DataFrame:
    """DeMark TD Setup 카운트 계산.

    - Sell Setup: Close(t) > Close(t-4) 연속 시 +1, 아니면 리셋
    - Buy Setup: Close(t) < Close(t-4) 연속 시 +1, 아니면 리셋

    Args:
        df: OHLCV DataFrame
        col: 비교할 가격 컬럼

    Returns:
        TD_Sell, TD_Buy 컬럼이 추가된 DataFrame
    """
    df = df.copy()
    n = len(df)
    sell = np.zeros(n)
    buy = np.zeros(n)
    prices = df[col].values

    for i in range(4, n):
        # Sell Setup (상승 피로)
        if prices[i] > prices[i - 4]:
            sell[i] = sell[i - 1] + 1
        else:
            sell[i] = 0

        # Buy Setup (하락 피로)
        if prices[i] < prices[i - 4]:
            buy[i] = buy[i - 1] + 1
        else:
            buy[i] = 0

    df["TD_Sell"] = sell.astype(int)
    df["TD_Buy"] = buy.astype(int)
    return df


def calc_elder_impulse(df: pd.DataFrame, ema_period: int = 13) -> pd.DataFrame:
    """Elder Impulse System 계산.

    - EMA 기울기와 MACD 히스토그램 기울기로 추세 판별
    - bull: 둘 다 상승
    - bear: 둘 다 하락
    - neutral: 혼조

    Args:
        df: OHLCV DataFrame
        ema_period: EMA 기간 (기본 13)

    Returns:
        EMA13, MACD, Impulse 컬럼이 추가된 DataFrame
    """
    df = df.copy()
    close = df["Close"]

    # EMA
    df["EMA"] = calc_ema(close, ema_period)

    # MACD (12, 26, 9)
    ema12 = calc_ema(close, 12)
    ema26 = calc_ema(close, 26)
    df["MACD"] = ema12 - ema26
    df["MACD_Signal"] = calc_ema(df["MACD"], 9)
    df["MACD_Hist"] = df["MACD"] - df["MACD_Signal"]

    # Impulse 판정
    ema_slope = df["EMA"].diff()
    hist_slope = df["MACD_Hist"].diff()

    impulse = pd.Series("neutral", index=df.index)
    impulse[(ema_slope > 0) & (hist_slope > 0)] = "bull"
    impulse[(ema_slope < 0) & (hist_slope < 0)] = "bear"
    df["Impulse"] = impulse

    return df


def add_indicators(
    df: pd.DataFrame, ma_period: int = 10, cmf_period: int = 4
) -> pd.DataFrame:
    """DataFrame에 지표 컬럼 추가.

    Args:
        df: OHLCV DataFrame
        ma_period: 이동평균 기간
        cmf_period: CMF 기간

    Returns:
        지표가 추가된 DataFrame
    """
    df = df.copy()
    df["MA"] = calc_ma(df["Close"], ma_period)
    df["CMF"] = calc_cmf(df, cmf_period)
    df["FG"] = calc_fear_greed(df)
    df["PrevHigh"] = df["High"].shift(1)
    df["PrevLow"] = df["Low"].shift(1)
    return df


def add_all_indicators(
    df: pd.DataFrame,
    ma_period: int = 10,
    cmf_period: int = 4,
    include_td: bool = True,
    include_elder: bool = True,
) -> pd.DataFrame:
    """모든 지표 추가 (기본 + DeMark + Elder).

    Args:
        df: OHLCV DataFrame
        ma_period: 이동평균 기간
        cmf_period: CMF 기간
        include_td: DeMark TD Setup 포함 여부
        include_elder: Elder Impulse 포함 여부

    Returns:
        모든 지표가 추가된 DataFrame
    """
    df = add_indicators(df, ma_period, cmf_period)

    if include_td:
        df = calc_td_setup(df)

    if include_elder:
        df = calc_elder_impulse(df)

    return df
