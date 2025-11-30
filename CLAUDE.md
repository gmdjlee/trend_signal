# krx_trend 패키지 명세서

> Claude Code 및 외부 프로그램 이식을 위한 기술 명세

## 개요

한국 주식 시장(KRX) 종목의 **주간 추세 전략 분석** 패키지입니다.
pykrx 라이브러리를 통해 데이터를 수집하고, 기술적 지표 기반 매수/매도 신호를 생성하며, 백테스트 및 시각화를 제공합니다.

---

## 설치 요구사항

```bash
pip install pykrx pandas numpy matplotlib
```

### 의존성

| 패키지 | 버전 | 용도 |
|--------|------|------|
| pykrx | ≥0.1.0 | KRX/네이버 금융 데이터 수집 |
| pandas | ≥1.5.0 | 데이터 처리 |
| numpy | ≥1.20.0 | 수치 계산 |
| matplotlib | ≥3.5.0 | 차트 시각화 |

---

## 패키지 구조

```
krx_trend/
├── __init__.py      # 통합 API (analyze, analyze_multi)
├── fetcher.py       # 데이터 수집 (pykrx)
├── indicators.py    # 기술적 지표 (CMF, FG, MA)
├── signals.py       # 매수/매도 신호, 백테스트
├── chart.py         # 차트 시각화
└── utils.py         # 유틸리티 (종목 조회, 리샘플링)
```

---

## 빠른 시작

### 기본 사용법

```python
from krx_trend import analyze, analyze_multi

# 단일 종목 분석
result = analyze("삼성전자")
result = analyze("005930", start="2023-01-01")

# 다중 종목 분석
results = analyze_multi(["삼성전자", "SK하이닉스", "NAVER"])
```

### 결과 활용

```python
result = analyze("삼성전자", plot=False, verbose=False)

# 결과 구조
result["code"]      # 종목코드: "005930"
result["name"]      # 종목명: "삼성전자"
result["df"]        # 지표/신호 포함 DataFrame
result["bt"]        # 백테스트 결과 DataFrame
result["summary"]   # 요약 통계 dict
```

---

## API 상세

### 1. 통합 API (`__init__.py`)

#### `analyze(query, start, end, ma_period, cmf_period, adjusted, plot, verbose)`

단일 종목 전략 분석.

| 파라미터 | 타입 | 기본값 | 설명 |
|----------|------|--------|------|
| `query` | str | 필수 | 종목명 또는 6자리 코드 |
| `start` | str \| None | None | 시작일 (YYYYMMDD 또는 YYYY-MM-DD) |
| `end` | str \| None | None | 종료일 |
| `ma_period` | int | 10 | 이동평균 기간 (주) |
| `cmf_period` | int | 4 | CMF 계산 기간 (주) |
| `adjusted` | bool | True | True=수정주가, False=일반주가 |
| `plot` | bool | True | 차트 표시 여부 |
| `verbose` | bool | True | 결과 출력 여부 |

**반환값**: `dict | None`
```python
{
    "code": str,           # 종목코드
    "name": str,           # 종목명
    "df": pd.DataFrame,    # 지표/신호 DataFrame
    "bt": pd.DataFrame,    # 백테스트 결과
    "summary": {
        "trades": int,     # 거래 횟수
        "avg_ret": float,  # 평균 수익률
        "cum_ret": float,  # 누적 수익률
        "win_rate": float  # 승률
    }
}
```

#### `analyze_multi(queries, ...)`

다중 종목 분석. 파라미터는 `analyze()`와 동일.

**반환값**: `dict[str, dict]` - {종목명: 분석결과}

---

### 2. 데이터 수집 (`fetcher.py`)

#### `fetch_ohlcv(query, start, end, period, adjusted)`

종목 OHLCV 데이터 수집.

| 파라미터 | 타입 | 기본값 | 설명 |
|----------|------|--------|------|
| `query` | str | 필수 | 종목명 또는 코드 |
| `start` | str \| None | None | 시작일 (기본: 3년 전) |
| `end` | str \| None | None | 종료일 (기본: 오늘) |
| `period` | str | "weekly" | "daily" 또는 "weekly" |
| `adjusted` | bool | True | 수정주가 여부 |

**반환값**: `tuple[pd.DataFrame | None, str | None]`
- 성공: (OHLCV DataFrame, 종목코드)
- 실패: (None, None)

**DataFrame 컬럼**: `Open`, `High`, `Low`, `Close`, `Volume`

**주의사항**:
- pykrx의 수정주가는 액면분할만 반영 (배당 재투자 미반영)
- yfinance와 약간의 가격 차이 발생 가능

---

### 3. 기술적 지표 (`indicators.py`)

#### `add_indicators(df, ma_period, cmf_period)`

DataFrame에 모든 지표 컬럼 추가.

| 파라미터 | 타입 | 기본값 | 설명 |
|----------|------|--------|------|
| `df` | pd.DataFrame | 필수 | OHLCV DataFrame |
| `ma_period` | int | 10 | 이동평균 기간 |
| `cmf_period` | int | 4 | CMF 기간 |

**추가되는 컬럼**:
| 컬럼 | 설명 |
|------|------|
| `MA` | 종가 이동평균 |
| `CMF` | Chaikin Money Flow |
| `FG` | Fear & Greed 지수 |
| `PrevHigh` | 전주 고가 |
| `PrevLow` | 전주 저가 |

#### `calc_ma(s, n)`

이동평균 계산.

```python
ma = calc_ma(df["Close"], 10)  # 10주 이동평균
```

#### `calc_cmf(df, n)`

Chaikin Money Flow 계산.

**공식**:
```
MF_Multiplier = ((Close - Low) - (High - Close)) / (High - Low)
MF_Volume = MF_Multiplier × Volume
CMF = SUM(MF_Volume, n) / SUM(Volume, n)
```

#### `calc_fear_greed(df)`

Fear & Greed 지수 계산.

**구성요소** (가중치):
| 요소 | 가중치 | 설명 |
|------|--------|------|
| 모멘텀 | 45% | 5주 로그 수익률 |
| 52주 포지션 | 45% | 52주 고저 대비 현재가 위치 |
| 거래량 급증 | 5% | 최근/과거 거래량 비율 |
| 변동성 스파이크 | 5% | 최근/과거 변동성 비율 (역방향) |

**출력 범위**: 약 -1.0 ~ +1.5
- `> 0.5`: 탐욕 구간
- `< -0.5`: 공포 구간

---

### 4. 신호 생성 (`signals.py`)

#### `generate_signals(df)`

매수/매도 신호 생성.

**매수 조건** (AND):
1. `High > PrevHigh` (전주 고가 돌파)
2. `Close > MA` (이동평균 상회)
3. `CMF > 0` (자금 유입)

**매도 조건** (AND):
1. `Low < PrevLow` (전주 저가 이탈)
2. `Close < MA` (이동평균 하회)
3. `CMF < 0` (자금 유출)

**추가되는 컬럼**:
| 컬럼 | 값 | 설명 |
|------|-----|------|
| `Buy` | 0/1 | 매수 신호 |
| `Sell` | 0/1 | 매도 신호 |
| `ActualSell` | 0/1 | 실제 청산 신호 (포지션 보유 후 첫 매도) |

#### `backtest(df, close_last)`

백테스트 실행.

| 파라미터 | 타입 | 기본값 | 설명 |
|----------|------|--------|------|
| `df` | pd.DataFrame | 필수 | 신호 포함 DataFrame |
| `close_last` | bool | True | 마지막 미청산 포지션 정리 여부 |

**반환 DataFrame 컬럼**:
| 컬럼 | 타입 | 설명 |
|------|------|------|
| `EntryDate` | datetime | 진입일 |
| `EntryPrice` | float | 진입가 (시가) |
| `ExitDate` | datetime | 청산일 |
| `ExitPrice` | float | 청산가 (종가) |
| `Return` | float | 개별 수익률 |
| `CumRet` | float | 누적 수익률 |

#### `summary(bt_df)`

백테스트 요약 통계 반환.

```python
{
    "trades": int,     # 총 거래 횟수
    "avg_ret": float,  # 평균 수익률
    "cum_ret": float,  # 누적 수익률 (최종값 - 1)
    "win_rate": float  # 승률 (수익 거래 비율)
}
```

#### `print_summary(bt_df, name)`

백테스트 결과 콘솔 출력.

---

### 5. 차트 시각화 (`chart.py`)

#### `plot_strategy(df, bt_df, title, figsize, show)`

전략 차트 시각화.

| 파라미터 | 타입 | 기본값 | 설명 |
|----------|------|--------|------|
| `df` | pd.DataFrame | 필수 | 지표/신호 DataFrame |
| `bt_df` | pd.DataFrame \| None | None | 백테스트 결과 |
| `title` | str | "" | 차트 제목 |
| `figsize` | tuple | (16, 5) | 그림 크기 |
| `show` | bool | True | plt.show() 호출 여부 |

**반환값**: `tuple[fig, ax1, ax2]`

**차트 구성**:
- 주축: 종가, 이동평균, 매수/매도 신호
- 보조축: Fear & Greed 지수
- 신호 마커:
  - 🔺 진한 빨강: 주요 매수 (실제 진입)
  - △ 연한 빨강: 보조 매수 (신호만)
  - 🔻 진한 파랑: 주요 매도 (실제 청산)
  - ▽ 연한 파랑: 보조 매도 (신호만)

#### `plot_multi(results, figsize, show)`

다중 종목 차트.

---

### 6. 유틸리티 (`utils.py`)

#### `to_code(query)`

종목명/코드 → 6자리 종목코드 변환.

```python
to_code("삼성전자")  # "005930"
to_code("005930")    # "005930"
to_code("삼성")      # "005930" (부분 매칭)
```

**반환값**: `str | None`

#### `to_name(code)`

종목코드 → 종목명 변환.

```python
to_name("005930")  # "삼성전자"
```

#### `get_stock_list()`

전체 종목 리스트 조회 (캐시됨).

**반환값**: `pd.DataFrame` with columns `["code", "name"]`

#### `resample_weekly(df)`

일봉 → 주봉 변환 (금요일 기준).

```python
weekly_df = resample_weekly(daily_df)
```

---

## 데이터 흐름

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  fetch_ohlcv │ ──▶ │add_indicators│ ──▶ │generate_signals│
│   (pykrx)   │     │  (지표계산)  │     │   (신호생성)   │
└─────────────┘     └─────────────┘     └─────────────┘
                                               │
                    ┌─────────────┐            ▼
                    │plot_strategy│ ◀── ┌─────────────┐
                    │   (차트)    │     │  backtest   │
                    └─────────────┘     │  (백테스트)  │
                                        └─────────────┘
```

---

## 사용 예시

### 커스텀 파이프라인

```python
from krx_trend import (
    fetch_ohlcv,
    add_indicators,
    generate_signals,
    backtest,
    plot_strategy
)

# 1. 데이터 수집
df, code = fetch_ohlcv("삼성전자", start="2022-01-01", period="weekly")

# 2. 지표 계산 (커스텀 파라미터)
df = add_indicators(df, ma_period=20, cmf_period=6)

# 3. 신호 생성
df = generate_signals(df)

# 4. 백테스트
bt = backtest(df, close_last=False)

# 5. 시각화
fig, ax1, ax2 = plot_strategy(df, bt, title="커스텀 분석", show=False)
fig.savefig("chart.png")
```

### 지표만 사용

```python
from krx_trend import fetch_ohlcv, calc_cmf, calc_fear_greed

df, _ = fetch_ohlcv("005930", period="daily")
df["CMF"] = calc_cmf(df, n=20)
df["FG"] = calc_fear_greed(df)
```

### 종목 검색

```python
from krx_trend import get_stock_list, to_code

# 전체 종목 리스트
stocks = get_stock_list()
print(stocks[stocks["name"].str.contains("삼성")])

# 종목코드 변환
code = to_code("SK하이닉스")  # "000660"
```

### Android/Chaquopy 통합

```python
# 차트 없이 데이터만 반환
from krx_trend import analyze

result = analyze("삼성전자", plot=False, verbose=False)
if result:
    data = {
        "code": result["code"],
        "name": result["name"],
        "trades": result["summary"]["trades"],
        "cum_ret": result["summary"]["cum_ret"],
        "win_rate": result["summary"]["win_rate"],
        "signals": result["df"][["Close", "Buy", "Sell", "FG"]].to_dict()
    }
```

---

## DataFrame 스키마

### OHLCV DataFrame (fetch_ohlcv 반환)

| 컬럼 | 타입 | 설명 |
|------|------|------|
| index | DatetimeIndex | 날짜 (금요일 기준 주봉) |
| Open | float | 시가 |
| High | float | 고가 |
| Low | float | 저가 |
| Close | float | 종가 |
| Volume | int | 거래량 |

### 지표 DataFrame (add_indicators 반환)

| 컬럼 | 타입 | 범위 | 설명 |
|------|------|------|------|
| MA | float | - | 이동평균 |
| CMF | float | -1 ~ +1 | Chaikin Money Flow |
| FG | float | -1 ~ +1.5 | Fear & Greed |
| PrevHigh | float | - | 전주 고가 |
| PrevLow | float | - | 전주 저가 |

### 신호 DataFrame (generate_signals 반환)

| 컬럼 | 타입 | 값 | 설명 |
|------|------|-----|------|
| Buy | int | 0/1 | 매수 신호 |
| Sell | int | 0/1 | 매도 신호 |
| ActualSell | int | 0/1 | 실제 청산 |

### 백테스트 DataFrame (backtest 반환)

| 컬럼 | 타입 | 설명 |
|------|------|------|
| EntryDate | datetime | 진입일 |
| EntryPrice | float | 진입가 |
| ExitDate | datetime | 청산일 |
| ExitPrice | float | 청산가 |
| Return | float | 수익률 |
| CumRet | float | 누적 수익률 |

---

## 전략 로직 상세

### 매수 조건

```
BUY = (High > PrevHigh) AND (Close > MA) AND (CMF > 0)
```

- **High > PrevHigh**: 상승 추세 확인 (전주 고점 돌파)
- **Close > MA**: 중기 추세 상승 확인
- **CMF > 0**: 자금 유입 확인 (매수세 우위)

### 매도 조건

```
SELL = (Low < PrevLow) AND (Close < MA) AND (CMF < 0)
```

- **Low < PrevLow**: 하락 추세 확인 (전주 저점 이탈)
- **Close < MA**: 중기 추세 하락 확인
- **CMF < 0**: 자금 유출 확인 (매도세 우위)

### 진입/청산 가격

- **진입**: 매수 신호 발생 주의 **시가(Open)**
- **청산**: 매도 신호 발생 주의 **종가(Close)**

---

## 제한사항

1. **한국 시장 전용**: pykrx는 KRX(한국거래소) 데이터만 지원
2. **수정주가 차이**: pykrx는 액면분할만 반영 (배당 재투자 미반영)
3. **주봉 기준**: 기본적으로 주간 데이터 사용 (일봉도 가능)
4. **실시간 미지원**: 장중 실시간 데이터 미지원
5. **네트워크 의존**: pykrx는 네이버 금융/KRX 서버 접속 필요

---

## 버전 정보

- **버전**: 1.0.0
- **Python**: ≥3.10
- **라이선스**: MIT