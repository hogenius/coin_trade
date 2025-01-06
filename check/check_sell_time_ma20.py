import pyupbit
import pandas as pd
import datetime

def get_revenue_rate( balances, ticker):
    revenue_rate = 0.0

    for coin in balances:
        # 티커 형태로 전환
        coin_ticker = coin['unit_currency'] + "-" + coin['currency']

        if ticker == coin_ticker:
            # 현재 시세
            now_price = pyupbit.get_current_price(coin_ticker)
            
            # 수익률 계산을 위한 형 변환
            revenue_rate = (now_price - float(coin['avg_buy_price'])) / float(coin['avg_buy_price']) * 100.0

    return revenue_rate

def check_sell_ma_process(coin_name, ma_period, isTest):
    
    # PyUpbit API를 통해 OHLCV 데이터 가져오기
    df = pyupbit.get_ohlcv(coin_name, count=(ma_period * 2) + 1)

    print(df)

    # 시가와 종가의 중간값 계산 (시가와 종가의 평균)
    df['mid_price'] = (df['open'] + df['close']) / 2

    if isTest == True:
        print(df)

    # ma_period일 이동평균선 계산 (중간값 기준)
    df['MA_PERIOD'] = df['mid_price'].rolling(window=ma_period).mean()

    if isTest == True:
        print(df)

    # 기울기 계산 (y2 - y1)로 간단하게 계산
    slopes = []
    ma_values = df['MA_PERIOD'].dropna().values  # NaN 제거
    
    if isTest == True:
        print(ma_values)

    # 단순 차이 계산으로 오케이인가?
    # 오케이다 왜냐하면 기울기라는게 원래 (y2 - y1) / (x2 - x1)인데,
    # x값은 시간값이라 항상 간격이 동일하기 때문에 1이기 때문이다.
    # 미래 - 과거 데이터로 기울기라고 간주할 수 있다.
    for i in range(1, len(ma_values)):
        slope = ma_values[i] - ma_values[i - 1]
        slopes.append(slope)

    if isTest == True:
        print(slopes)

    # 기울기의 평균 계산
    average_slope = sum(slopes) / len(slopes) if slopes else 0

    # 결과 출력
    if isTest == True:
        print(f"{coin_name} - 평균 기울기: {average_slope:.5f}")
    return average_slope

def check_sell_time_ma20(coin_info, balances, config, print_msg, isForce, isTest):
    coin_name = coin_info['name']
    now = datetime.datetime.now()
    end_time = now.replace(hour=7, minute=0, second=0, microsecond=0)
    start_time = end_time - datetime.timedelta(seconds=config.loop_sec*3)

    #매도 시간 KST 06:57 ~ 07:00
    is_sell_time = start_time < now < end_time
    if is_sell_time == True:
        revenue_rate = get_revenue_rate(balances, coin_name)
        if revenue_rate < 0:
            #팔아야할 시간인데, 수익률이 마이너스다??!
            average_slope = check_sell_ma_process(coin_info['name'], 20, isTest)
            if 0 < average_slope:
                #그런데 MA20 평균 기울기는 양수라면? 팔지말고 좀더 지켜보자.
                print_msg(f"[SELL_MA20] {coin_name} revenue_rate:{revenue_rate}이지만, MA20 기울기가 양수({average_slope})이므로 매도하지 않습니다.")
                is_sell_time = False
            else:
                print_msg(f"[SELL_MA20] {coin_name} revenue_rate:{revenue_rate}, MA20 기울기도 음수({average_slope})이므로 매도합니다.")


    return is_sell_time

# 예시 호출
#print(check_sell_ma_process("KRW-BTC", 60))

    