"""

변동성 돌파 전략(Volatility Breakout)
+
이동평균선 전략(Moving Average Line)

"""

import time
import pyupbit
import datetime
import find_best_k
import pandas
import msg_discord
from config import ConfigInfo
config = ConfigInfo.Instance()

def get_target_price(ticker, k):
    """변동성 돌파 전략으로 매수 목표가 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=2)
    target_price = df.iloc[0]['close'] + (df.iloc[0]['high'] - df.iloc[0]['low']) * k
    return target_price

def get_start_time(ticker):
    """시작 시간 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=1)
    start_time = df.index[0]
    return start_time

def get_balance(ticker):
    """잔고 조회"""
    balances = upbit.get_balances()
    for b in balances:
        if b['currency'] == ticker:
            if b['balance'] is not None:
                return float(b['balance'])
            else:
                return 0
    return 0

def get_current_price(ticker):
    """현재가 조회"""
    return pyupbit.get_orderbook(ticker=ticker)["orderbook_units"][0]["ask_price"]

def print_msg(msg, withDiscord=True):
    print(msg)
    if withDiscord:
        msg_discord.send(msg)

# login
upbit = pyupbit.Upbit(config.access,config.secret)

print_msg("autotrade start")

best_k = find_best_k.GetBestK()
print_msg(f"autotrade check best k {best_k}")
# 자동매매 시작
while True:
    try:

        now = datetime.datetime.now()
        start_time = get_start_time("KRW-BTC") # 09:00
        end_time = start_time + datetime.timedelta(days=1) # 09:00 + 1일

        # 9시부터 < 현재 < 담날08:59:50까지 돌도록
        if start_time < now < end_time - datetime.timedelta(seconds=config.loop_sec*2):

            df = pyupbit.get_ohlcv(config.coin_name, count=config.ma_3)
            df['MA_1'] = df['close'].rolling(config.ma_1).mean()
            df['MA_2'] = df['close'].rolling(config.ma_2).mean()
            #df['MA_3'] = df['close'].rolling(config.ma_3).mean()
            pandas.set_option('display.float_format', lambda x: '%.1f' % x)

            last_data = df.iloc[(len(df)-1)]
            data_ma_1 = last_data['MA_1']
            data_ma_2 = last_data['MA_2']
            #data_ma_3 = last_data['MA_3']

            #print(f"{config.ma_1}ma:{data_ma_1}, {config.ma_2}ma:{data_ma_2}, {config.ma_3}ma:{data_ma_3}")
            print(f"{config.ma_1}ma:{data_ma_1}, {config.ma_2}ma:{data_ma_2}")
            #is_regulat_arr = (data_ma_3 < data_ma_2 < data_ma_1)
            is_regulat_arr = (data_ma_2 < data_ma_1)
            print(f"is_regulat_arr : {is_regulat_arr}")

            target_price = get_target_price("KRW-BTC", best_k)
            current_price = get_current_price("KRW-BTC")
            if is_regulat_arr and target_price < current_price:
                krw = get_balance("KRW")
                if krw > 5000:
                    buy_krw = krw*0.9995
                    upbit.buy_market_order("KRW-BTC", buy_krw)
                    print_msg(f"autotrade buy_market_order {buy_krw}")
        else:
            #전량 매도.
            btc = get_balance("BTC")
            if btc > 0.00008:
                sell_btc = btc*0.9995
                upbit.sell_market_order("KRW-BTC", sell_btc)
                print_msg(f"autotrade sell_market_order {sell_btc}")
            
            best_k = find_best_k.GetBestK()
            print_msg(f"autotrade check best k {best_k}")

        #test = 1
        #print(f"autotrade check")

        #best_k = find_best_k.GetBestK()
        #print(f"autotrade check best k {best_k}")
        time.sleep(config.loop_sec)
    except Exception as e:
        print(e)
        time.sleep(config.loop_sec)