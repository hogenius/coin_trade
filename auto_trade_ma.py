"""

이동평균선 전략(Moving Average Line)

"""

import time
import pyupbit
import pandas
from config import ConfigInfo
config = ConfigInfo()

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

# login
upbit = pyupbit.Upbit(config.access, config.secret)
print("autotrade start")

while True:
    
    try:
        df = pyupbit.get_ohlcv(config.coin_name, count=config.ma_3)
        df['MA_1'] = df['close'].rolling(config.ma_1).mean()
        df['MA_2'] = df['close'].rolling(config.ma_2).mean()
        df['MA_3'] = df['close'].rolling(config.ma_3).mean()
        pandas.set_option('display.float_format', lambda x: '%.1f' % x)

        last_data = df.iloc[(len(df)-1)]
        data_ma_1 = last_data['MA_1']
        data_ma_2 = last_data['MA_2']
        data_ma_3 = last_data['MA_3']

        print(f"{config.ma_1}ma:{data_ma_1}, {config.ma_2}ma:{data_ma_2}, {config.ma_3}ma:{data_ma_3}")

        if data_ma_3 < data_ma_2 < data_ma_1:
            #50일, 30일 , 10일 정배열이라면?
            print("order buy!!!")
            krw = get_balance("KRW")
            if krw > 5000:
                buy_krw = krw*0.9995
                #upbit.buy_market_order("KRW-BTC", buy_krw)
                print(f"autotrade buy_market_order {buy_krw}")
        elif data_ma_1 <= data_ma_2:
            #10일 30일 이평선이 교차했다?
            print("order sell!!!")
            btc = get_balance("BTC")
            if btc > 0.00008:
                sell_btc = btc*0.9995
                #upbit.sell_market_order("KRW-BTC", sell_btc)
                print(f"autotrade sell_market_order {sell_btc}")
        else:
            print("do nothing..")

        time.sleep(config.ma_check_sec)
    except Exception as e:
        print(e)
        time.sleep(config.ma_check_sec)
