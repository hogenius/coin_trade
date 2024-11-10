import pyupbit
import pandas as pd

def check_sell_ma_process(coin_name, period):
    
    # PyUpbit API를 통해 OHLCV 데이터 가져오기
    df = pyupbit.get_ohlcv(coin_name, count=period + 1)

    print(df)

    # 시가와 종가의 중간값 계산 (시가와 종가의 평균)
    df['mid_price'] = (df['open'] + df['close']) / 2

    print(df)

    # 20일 이동평균선 계산 (중간값 기준)
    df['MA_20'] = df['mid_price'].rolling(window=20).mean()

    print(df)

    # 기울기 계산 (y2 - y1)로 간단하게 계산
    slopes = []
    ma_values = df['MA_20'].dropna().values  # NaN 제거
    print(ma_values)

    for i in range(1, len(ma_values)):
        slope = ma_values[i] - ma_values[i - 1]
        slopes.append(slope)

    print(slopes)

    # 기울기의 평균 계산
    average_slope = sum(slopes) / len(slopes) if slopes else 0

    # 결과 출력
    print(f"{coin_name} - 평균 기울기: {average_slope:.5f}")
    return average_slope

def check_sell_ma(coin_info, balances, config, print_msg, isForce, isTest):

    coin_name = coin_info['name']
    period = 20
    check_sell_ma_process(coin_name, period)

# 예시 호출
print(check_sell_ma_process("KRW-BTC", 60))

    