
import time
import pyupbit
import datetime
import find_best_k
import pandas
import msg_discord
from config import ConfigInfo
from statistics import stdev
config = ConfigInfo()
is_test = True
list_coin_info = []
list_coin_info_warning = []

def CheckSpike():

    tickers = pyupbit.get_tickers("KRW", True)

    for ticker in tickers:
        if 'CAUTION' in ticker['market_warning']:
            list_coin_info_warning.append(ticker)
            continue

        list_coin_info.append(ticker)

    print(list_coin_info)
    print(f"list_coin_info count: {len(list_coin_info)}")
    print(list_coin_info_warning)
    print(f"list_coin_info_warning count: {len(list_coin_info_warning)}")

OUTLIER_COUNT = 5

def CheckTicker(ticker):

    df = pyupbit.get_ohlcv(ticker, interval="minutes3", count=200)
    print(df)


    #df = pyupbit.get_ohlcv(ticker, interval="minutes3", count=10)
    #print(df)

    #df = pyupbit.get_ohlcv(ticker, interval="minutes3", count=1)
    #print(df)

    col_one_list = df['volume'].tolist()
    print(col_one_list)
    print(f"col_one_list count: {len(col_one_list)}")

    col_one_list2 = col_one_list[OUTLIER_COUNT:len(col_one_list) - OUTLIER_COUNT]
    print(col_one_list2)
    print(f"col_one_list2 count: {len(col_one_list2)}")

    prev_stdev_vol = stdev(col_one_list)
    print(f"col_one_list stdev: {stdev(col_one_list)}")
    print(f"col_one_list2 stdev: {stdev(col_one_list2)}")

CheckTicker('KRW-BTC')

# 체크 시작
'''
while True:
    try:
        CheckSpike()

        time.sleep(config.loop_sec)
    except Exception as e:
        print(e)
        time.sleep(config.loop_sec)
'''