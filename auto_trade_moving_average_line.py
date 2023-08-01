import time
import pyupbit
import yaml
import pandas

access = ""
secret = ""
coin_name = ""
ma_1 = 0
ma_2 = 0
ma_3 = 0
ma_check_sec = 0

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

# config load
with open('config.yaml') as f:
    config_data = yaml.load(f, Loader=yaml.FullLoader)
    access = config_data['key_access']
    secret = config_data['key_secret']
    coin_name = config_data['coin_name']
    ma_1 = config_data['ma_line_1']
    ma_2 = config_data['ma_line_2']
    ma_3 = config_data['ma_line_3']
    ma_check_sec = config_data['ma_check_sec']

# login
upbit = pyupbit.Upbit(access, secret)
print("autotrade start")

while True:
    
    try:
        df = pyupbit.get_ohlcv(coin_name, count=ma_3)
        df['MA_1'] = df['close'].rolling(ma_1).mean()
        df['MA_2'] = df['close'].rolling(ma_2).mean()
        df['MA_3'] = df['close'].rolling(ma_3).mean()
        pandas.set_option('display.float_format', lambda x: '%.1f' % x)

        last_data = df.iloc[(len(df)-1)]
        data_ma_1 = last_data['MA_1']
        data_ma_2 = last_data['MA_2']
        data_ma_3 = last_data['MA_3']

        print(f"{ma_1}ma:{data_ma_1}, {ma_2}ma:{data_ma_2}, {ma_3}ma:{data_ma_3}")

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

        time.sleep(ma_check_sec)
    except Exception as e:
        print(e)
        time.sleep(ma_check_sec)
