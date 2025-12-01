"""차트 시각화."""

import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd

# 기본 설정
mpl.rcParams.update(mpl.rcParamsDefault)
mpl.rcParams["axes.unicode_minus"] = False


def plot_strategy(
    df: pd.DataFrame,
    bt_df: pd.DataFrame | None = None,
    title: str = "",
    figsize: tuple = (16, 5),
    show: bool = True,
) -> tuple:
    """전략 차트 시각화.

    Args:
        df: 지표 및 신호가 포함된 DataFrame
        bt_df: 백테스트 결과 (옵션)
        title: 차트 제목
        figsize: 그림 크기
        show: plt.show() 호출 여부

    Returns:
        (fig, ax1, ax2) 튜플
    """
    fig, ax1 = plt.subplots(figsize=figsize)

    # 가격 및 이동평균
    ax1.plot(df.index, df["Close"], label="종가", color="black")
    if "MA" in df.columns:
        ax1.plot(df.index, df["MA"], label="MA", linestyle="--", color="gray")

    # 매수/매도 신호 인덱스 분류
    if bt_df is not None and not bt_df.empty:
        primary_buy = bt_df["EntryDate"]
    else:
        primary_buy = pd.Index([])

    if "Buy" in df.columns:
        all_buy = df.index[df["Buy"] == 1]
        extra_buy = all_buy.difference(primary_buy)

        # 보조 매수 (연한 빨강)
        if len(extra_buy):
            ax1.scatter(
                extra_buy,
                df.loc[extra_buy, "Close"],
                marker="^",
                s=60,
                alpha=0.4,
                color="red",
                label="보조 매수",
            )

        # 주요 매수 (진한 빨강)
        if len(primary_buy):
            ax1.scatter(
                primary_buy,
                df.loc[primary_buy, "Close"],
                marker="^",
                s=100,
                alpha=1.0,
                color="darkred",
                label="매수",
            )

    if "ActualSell" in df.columns:
        primary_sell = df.index[df["ActualSell"] == 1]
        all_sell = df.index[df["Sell"] == 1]
        extra_sell = all_sell.difference(primary_sell)

        # 보조 매도 (연한 파랑)
        if len(extra_sell):
            ax1.scatter(
                extra_sell,
                df.loc[extra_sell, "Close"],
                marker="v",
                s=60,
                alpha=0.4,
                color="blue",
                label="보조 매도",
            )

        # 주요 매도 (진한 파랑)
        if len(primary_sell):
            ax1.scatter(
                primary_sell,
                df.loc[primary_sell, "Close"],
                marker="v",
                s=100,
                alpha=1.0,
                color="darkblue",
                label="매도",
            )

    ax1.set_title(title or "주간 추세 전략")
    ax1.set_xlabel("날짜")
    ax1.set_ylabel("가격")
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc="upper left")

    # Fear & Greed (보조 축)
    ax2 = None
    if "FG" in df.columns:
        ax2 = ax1.twinx()
        ax2.plot(df.index, df["FG"], color="orange", alpha=0.7, label="F&G")
        ax2.axhline(0.5, linestyle="--", color="red", alpha=0.5)
        ax2.axhline(-0.5, linestyle="--", color="green", alpha=0.5)
        ax2.set_ylabel("Fear & Greed")
        ax2.legend(loc="upper right")

    plt.tight_layout()

    if show:
        plt.show()

    return fig, ax1, ax2


def plot_td_setup(
    df: pd.DataFrame, title: str = "", figsize: tuple = (16, 5), show: bool = True
) -> tuple:
    """DeMark TD Setup 차트.

    Args:
        df: TD_Sell, TD_Buy 컬럼이 포함된 DataFrame
        title: 차트 제목
        figsize: 그림 크기
        show: plt.show() 호출 여부

    Returns:
        (fig, ax1, ax2) 튜플
    """
    fig, ax1 = plt.subplots(figsize=figsize)

    # 종가
    ax1.plot(df.index, df["Close"], color="black", label="종가")
    ax1.set_title(title or "DeMark TD Setup")
    ax1.set_xlabel("날짜")
    ax1.set_ylabel("가격")
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc="upper left")

    # TD 카운트 (보조 축)
    ax2 = ax1.twinx()
    if "TD_Sell" in df.columns:
        ax2.plot(df.index, df["TD_Sell"], color="red", alpha=0.8, label="TD Sell")
    if "TD_Buy" in df.columns:
        ax2.plot(df.index, df["TD_Buy"], color="blue", alpha=0.8, label="TD Buy")

    ax2.set_ylabel("TD Setup Count", color="gray")
    ax2.tick_params(axis="y", labelcolor="gray")

    # Y축 범위 설정
    max_td = 0
    if "TD_Sell" in df.columns:
        max_td = max(max_td, df["TD_Sell"].max())
    if "TD_Buy" in df.columns:
        max_td = max(max_td, df["TD_Buy"].max())
    ax2.set_ylim(0, max_td + 2)
    ax2.legend(loc="upper right")

    plt.tight_layout()

    if show:
        plt.show()

    return fig, ax1, ax2


def plot_elder_impulse(
    df: pd.DataFrame, title: str = "", figsize: tuple = (16, 5), show: bool = True
) -> tuple:
    """Elder Impulse System 차트.

    Args:
        df: EMA, Impulse 컬럼이 포함된 DataFrame
        title: 차트 제목
        figsize: 그림 크기
        show: plt.show() 호출 여부

    Returns:
        (fig, ax) 튜플
    """
    fig, ax = plt.subplots(figsize=figsize)

    # 종가 및 EMA
    ax.plot(df.index, df["Close"], linewidth=1.0, label="종가", color="black")
    if "EMA" in df.columns:
        ax.plot(
            df.index,
            df["EMA"],
            linestyle="--",
            linewidth=1.0,
            label="EMA13",
            color="gray",
        )

    # Impulse 색상 표시
    if "Impulse" in df.columns:
        bull_idx = df.index[df["Impulse"] == "bull"]
        bear_idx = df.index[df["Impulse"] == "bear"]
        neutral_idx = df.index[df["Impulse"] == "neutral"]

        if len(neutral_idx):
            ax.scatter(
                neutral_idx,
                df.loc[neutral_idx, "Close"],
                s=30,
                alpha=0.7,
                color="gray",
                label="Neutral",
            )
        if len(bull_idx):
            ax.scatter(
                bull_idx,
                df.loc[bull_idx, "Close"],
                s=40,
                alpha=0.9,
                color="green",
                label="Bullish",
            )
        if len(bear_idx):
            ax.scatter(
                bear_idx,
                df.loc[bear_idx, "Close"],
                s=40,
                alpha=0.9,
                color="red",
                label="Bearish",
            )

    ax.set_title(title or "Elder Impulse System")
    ax.set_xlabel("날짜")
    ax.set_ylabel("가격")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="upper left")

    plt.tight_layout()

    if show:
        plt.show()

    return fig, ax


def plot_multi(results: dict, figsize: tuple = (16, 4), show: bool = True) -> list:
    """다중 종목 차트.

    Args:
        results: {종목명: {"df": DataFrame, "bt": bt_df}} 딕셔너리
        figsize: 개별 차트 크기
        show: plt.show() 호출 여부

    Returns:
        (fig, ax1, ax2) 튜플 리스트
    """
    figs = []
    for name, data in results.items():
        df = data.get("df")
        bt = data.get("bt")
        if df is not None:
            figs.append(plot_strategy(df, bt, title=name, figsize=figsize, show=show))
    return figs
