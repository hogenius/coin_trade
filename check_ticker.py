
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
list_ticker = []
list_ticker_warning = []
list_spike = []

def print_msg(msg, withDiscord=True):
    if is_test:
        msg = 'TestMode:' + msg
    print(msg)
    if withDiscord:
        msg_discord.send(msg)

def MakeTickerList(listTicker, listTickerWarning):

    listTicker.clear()
    listTickerWarning.clear()

    tickers = pyupbit.get_tickers("KRW", True)

    for ticker in tickers:
        if 'CAUTION' in ticker['market_warning']:
            listTickerWarning.append(ticker)
            continue

        listTicker.append(ticker)

    #print(list_ticker)
    #print(f"list_coin_info count: {len(list_ticker)}")
    #print(list_ticker_warning)
    #print(f"list_coin_info_warning count: {len(list_ticker_warning)}")

OUTLIER_COUNT = 3

def CheckTicker(ticker, listTickerSpike):

    print(f"CheckTicker:{ticker}")
    listTickerSpike.clear()
    df = pyupbit.get_ohlcv(ticker['market'], interval="minutes3", count=200)
    #print(df)

    list_volume = df['volume'].tolist()
    #print(list_volume)
    #print(f"col_one_list count: {len(col_one_list)}")

    #앞 뒤 모두 OUTLIER_COUNT 수만큼 지움.
    #col_one_list2 = col_one_list[OUTLIER_COUNT:len(col_one_list) - OUTLIER_COUNT]
    #print(col_one_list2)
    #print(f"col_one_list2 count: {len(col_one_list2)}")

    #앞에만 OUTLIER_COUNT 수만큼 지움.
    #col_one_list3 = col_one_list[OUTLIER_COUNT:len(col_one_list)]
    #print(col_one_list3)
    #print(f"col_one_list2 count: {len(col_one_list3)}")

    #뒤에만 OUTLIER_COUNT 수만큼 지움.
    list_volume_before = list_volume[0:len(list_volume) - OUTLIER_COUNT]
    #print(col_one_list4)
    #print(f"col_one_list2 count: {len(col_one_list4)}")

    stdev_volume_before = stdev(list_volume_before)
    stdev_volume = stdev(list_volume)

    if (stdev_volume_before * 2.0) < stdev_volume:
        listTickerSpike.append({
            'name':ticker, 
            'stdev_volume_before':stdev_volume_before,
            'stdev_volume':stdev_volume
            })
        
print_msg(f"check ticker start")

# 체크 시작
while True:
    try:
        MakeTickerList(list_ticker, list_ticker_warning)

        for ticker in list_ticker:
            CheckTicker(ticker, list_spike)
            time.sleep(0.1)
        
        if(0 < len(list_spike) ):
            print_msg(f"spike coin find!! : {list_spike}")
        #else:
        #    print_msg("no spike coin..")

        time.sleep(config.loop_check_sec)
    except Exception as e:
        print(e)
        time.sleep(config.loop_check_sec)
