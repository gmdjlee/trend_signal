"""KRX 추세 분석 패키지.

한국 주식 시장 종목의 주간 추세 전략 분석 도구.

사용 예시:
    from krx_trend import analyze, analyze_multi

    # 단일 종목 분석
    result = analyze("삼성전자")

    # 다중 종목 분석
    results = analyze_multi(["삼성전자", "SK하이닉스", "005930"])

    # DeMark/Elder 포함 전체 분석
    result = analyze_full("삼성전자")
"""

from chart import plot_elder_impulse, plot_multi, plot_strategy, plot_td_setup
from fetcher import fetch_multi_period, fetch_ohlcv
from indicators import (
    add_all_indicators,
    add_indicators,
    calc_cmf,
    calc_elder_impulse,
    calc_ema,
    calc_fear_greed,
    calc_ma,
    calc_td_setup,
)
from signals import backtest, generate_signals, print_summary, summary
from utils import (
    filter_period,
    get_stock_list,
    resample_monthly,
    resample_weekly,
    to_code,
    to_name,
)


def analyze(
    query: str,
    start: str | None = None,
    end: str | None = None,
    ma_period: int = 10,
    cmf_period: int = 4,
    adjusted: bool = True,
    plot: bool = True,
    verbose: bool = True,
) -> dict | None:
    """단일 종목 전략 분석.

    Args:
        query: 종목명 또는 코드
        start: 시작일 (YYYYMMDD 또는 YYYY-MM-DD)
        end: 종료일
        ma_period: 이동평균 기간
        cmf_period: CMF 기간
        adjusted: True=수정주가, False=일반주가
        plot: 차트 표시 여부
        verbose: 결과 출력 여부

    Returns:
        분석 결과 딕셔너리 {"code", "name", "df", "bt", "summary"} 또는 None
    """
    # 1) 데이터 수집
    df, code = fetch_ohlcv(query, start, end, period="weekly", adjusted=adjusted)
    if df is None:
        return None

    name = f"{to_name(code)} ({code})"

    # 2) 지표 계산
    df = add_indicators(df, ma_period, cmf_period)

    # 3) 신호 생성
    df = generate_signals(df)

    # 4) 백테스트
    bt = backtest(df)

    # 5) 출력
    if verbose:
        print_summary(bt, name)

    # 6) 차트
    if plot:
        plot_strategy(df, bt, title=name)

    return {
        "code": code,
        "name": to_name(code),
        "df": df,
        "bt": bt,
        "summary": summary(bt),
    }


def analyze_full(
    query: str,
    start: str | None = None,
    end: str | None = None,
    ma_period: int = 10,
    cmf_period: int = 4,
    adjusted: bool = True,
    plot: bool = True,
    verbose: bool = True,
) -> dict | None:
    """전체 분석 (기본 전략 + DeMark + Elder Impulse).

    일봉/주봉/월봉 데이터에 대해 모든 지표를 계산하고
    차트를 생성합니다.

    Args:
        query: 종목명 또는 코드
        start: 시작일
        end: 종료일
        ma_period: 이동평균 기간
        cmf_period: CMF 기간
        adjusted: 수정주가 여부
        plot: 차트 표시 여부
        verbose: 결과 출력 여부

    Returns:
        {"code", "name", "daily", "weekly", "monthly", "bt", "summary"} 또는 None
    """
    # 1) 다중 기간 데이터 수집
    data = fetch_multi_period(query, start, end, adjusted)
    if data is None:
        return None

    code = data["code"]
    name = f"{to_name(code)} ({code})"

    daily = data["daily"]
    weekly = data["weekly"]
    monthly = data["monthly"]

    # 2) 주봉 기본 지표 + 신호
    weekly = add_indicators(weekly, ma_period, cmf_period)
    weekly = generate_signals(weekly)
    bt = backtest(weekly)

    # 3) DeMark TD Setup (일봉/주봉/월봉)
    daily = calc_td_setup(daily)
    weekly = calc_td_setup(weekly)
    monthly = calc_td_setup(monthly)

    # 4) Elder Impulse (주봉)
    weekly = calc_elder_impulse(weekly)

    # 5) 출력
    if verbose:
        print_summary(bt, name)

    # 6) 차트
    if plot:
        # 기본 전략 차트
        plot_strategy(weekly, bt, title=f"{name} 주간 전략")

        # Elder Impulse (최근 1년)
        weekly_1y = filter_period(weekly, years=1)
        if not weekly_1y.empty:
            plot_elder_impulse(weekly_1y, title=f"{name} Elder Impulse (주봉, 1년)")

        # TD Setup - 주봉 (최근 1년)
        if not weekly_1y.empty:
            plot_td_setup(weekly_1y, title=f"{name} TD Setup (주봉, 1년)")

        # TD Setup - 일봉 (최근 1년)
        daily_1y = filter_period(daily, years=1)
        if not daily_1y.empty:
            plot_td_setup(daily_1y, title=f"{name} TD Setup (일봉, 1년)")

        # TD Setup - 월봉 (전체)
        if not monthly.empty:
            plot_td_setup(monthly, title=f"{name} TD Setup (월봉, 전체)")

    return {
        "code": code,
        "name": to_name(code),
        "daily": daily,
        "weekly": weekly,
        "monthly": monthly,
        "bt": bt,
        "summary": summary(bt),
    }


def analyze_multi(
    queries: list[str],
    start: str | None = None,
    end: str | None = None,
    ma_period: int = 10,
    cmf_period: int = 4,
    adjusted: bool = True,
    plot: bool = True,
    verbose: bool = True,
) -> dict:
    """다중 종목 전략 분석.

    Args:
        queries: 종목명 또는 코드 리스트
        start, end, ma_period, cmf_period: analyze()와 동일
        adjusted: True=수정주가, False=일반주가
        plot: 차트 표시 여부
        verbose: 결과 출력 여부

    Returns:
        {종목명: 분석결과} 딕셔너리
    """
    results = {}
    for q in queries:
        result = analyze(
            q, start, end, ma_period, cmf_period, adjusted, plot=False, verbose=verbose
        )
        if result:
            results[result["name"]] = result

    if plot and results:
        plot_multi({k: {"df": v["df"], "bt": v["bt"]} for k, v in results.items()})

    print(f"\n=== 분석 완료: {len(results)}/{len(queries)} 종목 ===")
    return results


__all__ = [
    # 통합 API
    "analyze",
    "analyze_full",
    "analyze_multi",
    # 데이터 수집
    "fetch_ohlcv",
    "fetch_multi_period",
    # 지표
    "add_indicators",
    "add_all_indicators",
    "calc_cmf",
    "calc_fear_greed",
    "calc_ma",
    "calc_ema",
    "calc_td_setup",
    "calc_elder_impulse",
    # 신호
    "generate_signals",
    "backtest",
    "summary",
    "print_summary",
    # 차트
    "plot_strategy",
    "plot_multi",
    "plot_td_setup",
    "plot_elder_impulse",
    # 유틸
    "to_code",
    "to_name",
    "get_stock_list",
    "resample_weekly",
    "resample_monthly",
    "filter_period",
]
