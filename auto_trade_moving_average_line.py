import time
import pyupbit
import yaml
import pandas

access = ""
secret = ""

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

# login
upbit = pyupbit.Upbit(access, secret)
print("autotrade start")

while True:

    try:
        df = pyupbit.get_ohlcv("KRW-BTC", count=50)
        df['10MA'] = df['close'].rolling(10).mean()
        df['30MA'] = df['close'].rolling(30).mean()
        df['50MA'] = df['close'].rolling(50).mean()
        pandas.set_option('display.float_format', lambda x: '%.1f' % x)
        
        last_data = df.iloc[(len(df)-1)]
        data_10ma = last_data['10MA']
        data_30ma = last_data['30MA']
        data_50ma = last_data['50MA']

        print(f"10ma:{data_10ma}, 30ma:{data_30ma}, 50ma:{data_50ma}")

        if data_50ma < data_30ma < data_10ma:
            #50일, 30일 , 10일 정배열이라면?
            print("order buy!!!")
            krw = get_balance("KRW")
            if krw > 5000:
                buy_krw = krw*0.9995
                #upbit.buy_market_order("KRW-BTC", buy_krw)
                print(f"autotrade buy_market_order {buy_krw}")
        elif data_10ma < data_30ma:
            #10일 30일 이평선이 교차했다?
            print("order sell!!!")
            btc = get_balance("BTC")
            if btc > 0.00008:
                sell_btc = btc*0.9995
                #upbit.sell_market_order("KRW-BTC", sell_btc)
                print(f"autotrade sell_market_order {sell_btc}")
        else:
            print("do nothing..")

        time.sleep(60)
    except Exception as e:
        print(e)
        time.sleep(60)