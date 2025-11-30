"""신호 생성: 매수/매도 신호, 백테스트."""

import pandas as pd


def generate_signals(df: pd.DataFrame) -> pd.DataFrame:
    """매수/매도 신호 생성.

    매수 조건: 고가 > 전주 고가, 종가 > MA, CMF > 0
    매도 조건: 저가 < 전주 저가, 종가 < MA, CMF < 0

    Args:
        df: 지표가 포함된 DataFrame (add_indicators 적용 후)

    Returns:
        신호 컬럼이 추가된 DataFrame
    """
    df = df.copy()

    # 기본 신호 (원본과 동일한 방식: .loc[] 사용으로 NaN 행 보존)
    df["Buy"] = 0
    df["Sell"] = 0
    df["ActualSell"] = 0

    df.loc[
        (df["High"] > df["PrevHigh"]) & (df["Close"] > df["MA"]) & (df["CMF"] > 0),
        "Buy",
    ] = 1

    df.loc[
        (df["Low"] < df["PrevLow"]) & (df["Close"] < df["MA"]) & (df["CMF"] < 0), "Sell"
    ] = 1

    # 실제 매도 신호 (포지션 보유 후 첫 매도만)
    in_pos = False
    for i in range(1, len(df)):
        if not in_pos and df.iloc[i]["Buy"] == 1:
            in_pos = True
        elif in_pos and df.iloc[i]["Sell"] == 1:
            df.loc[df.index[i], "ActualSell"] = 1
            in_pos = False

    return df


def backtest(df: pd.DataFrame, close_last: bool = True) -> pd.DataFrame:
    """백테스트 실행.

    Args:
        df: 신호가 포함된 DataFrame
        close_last: 마지막 미청산 포지션 정리 여부

    Returns:
        거래 내역 DataFrame (EntryDate, EntryPrice, ExitDate, ExitPrice, Return, CumRet)
    """
    entries, exits = [], []
    in_pos = False
    entry_date, entry_price = None, None

    for i in range(1, len(df)):
        row = df.iloc[i]

        if not in_pos and row["Buy"] == 1:
            entry_date = row.name
            entry_price = row["Open"]
            in_pos = True
        elif in_pos and row["Sell"] == 1:
            entries.append((entry_date, entry_price))
            exits.append((row.name, row["Close"]))
            in_pos = False

    # 미청산 포지션 처리
    if in_pos and close_last:
        entries.append((entry_date, entry_price))
        exits.append((df.iloc[-1].name, df.iloc[-1]["Close"]))

    if not entries:
        return pd.DataFrame(
            columns=[
                "EntryDate",
                "EntryPrice",
                "ExitDate",
                "ExitPrice",
                "Return",
                "CumRet",
            ]
        )

    result = pd.DataFrame(entries, columns=["EntryDate", "EntryPrice"])
    result["ExitDate"], result["ExitPrice"] = zip(*exits)
    result["Return"] = (result["ExitPrice"] - result["EntryPrice"]) / result[
        "EntryPrice"
    ]
    result["CumRet"] = (1 + result["Return"]).cumprod()

    return result


def summary(bt_df: pd.DataFrame) -> dict:
    """백테스트 요약 통계.

    Returns:
        trades, avg_ret, cum_ret, win_rate 포함 딕셔너리
    """
    if bt_df.empty:
        return {"trades": 0, "avg_ret": 0, "cum_ret": 0, "win_rate": 0}

    return {
        "trades": len(bt_df),
        "avg_ret": bt_df["Return"].mean(),
        "cum_ret": bt_df["CumRet"].iloc[-1] - 1,
        "win_rate": (bt_df["Return"] > 0).mean(),
    }


def print_summary(bt_df: pd.DataFrame, name: str = "") -> None:
    """백테스트 결과 출력."""
    s = summary(bt_df)
    title = f" {name} " if name else ""
    print(f"\n{'=' * 20}{title}{'=' * 20}")

    if s["trades"] == 0:
        print("거래 없음")
        return

    print(bt_df.to_string(index=False))
    print(f"\n거래 횟수: {s['trades']}")
    print(f"평균 수익률: {s['avg_ret']:.2%}")
    print(f"누적 수익률: {s['cum_ret']:.2%}")
    print(f"승률: {s['win_rate']:.2%}")
