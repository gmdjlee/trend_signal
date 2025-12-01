"""사용 예시: KRX 추세 분석 패키지.

실행: python example.py
"""

from init import analyze_full

# === 단일 종목 분석 ===
# 종목명 또는 6자리 코드 모두 사용 가능
# result = analyze("삼성전자")

# 날짜 범위 지정
# result = analyze("005930", start="2023-01-01", end="2025-12-31")
result = analyze_full("005930", start="2023-01-01", adjusted=False)

# # 파라미터 조정 (MA 20주, CMF 6주)
# result = analyze("SK하이닉스", ma_period=20, cmf_period=6)

# # 차트/출력 없이 데이터만
# result = analyze("NAVER", plot=False, verbose=False)
# if result:
#     print(f"종목: {result['name']}")
#     print(f"누적수익률: {result['summary']['cum_ret']:.2%}")


# # === 다중 종목 분석 ===
# stocks = ["삼성전자", "SK하이닉스", "NAVER", "카카오"]
# results = analyze_multi(stocks)

# # 결과 활용
# for name, data in results.items():
#     s = data["summary"]
#     print(
#         f"{name}: 거래 {s['trades']}회, 승률 {s['win_rate']:.1%}, 누적 {s['cum_ret']:.1%}"
#     )


# # === 개별 모듈 활용 ===
# from krx_trend import (
#     add_indicators,
#     backtest,
#     fetch_ohlcv,
#     generate_signals,
#     plot_strategy,
#     to_code,
#     to_name,
# )

# # 종목 코드 조회
# code = to_code("삼성전자")  # '005930'
# name = to_name("005930")  # '삼성전자'

# # 커스텀 파이프라인
# df, code = fetch_ohlcv("현대차", start="2022-01-01")
# if df is not None:
#     df = add_indicators(df, ma_period=15)
#     df = generate_signals(df)
#     bt = backtest(df)
#     plot_strategy(df, bt, title=f"{to_name(code)} 커스텀 분석")
