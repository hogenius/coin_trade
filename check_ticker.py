import asyncio
#pip install schedule
import schedule

import time
import pyupbit
import datetime
import find_best_k
import pandas
import msg_discord
from config import ConfigInfo
from statistics import stdev
config = ConfigInfo.Instance()
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

async def CheckTicker(ticker, listTickerSpike, interval, checkCount):

    print(f"CheckTicker:{ticker['market']}, interval:{interval}, checkCount:{checkCount}")
    listTickerSpike.clear()
    df = pyupbit.get_ohlcv(ticker['market'], interval=interval, count=checkCount)
    #print(df)

    check_count = 3
    while df is None and 0 < check_count:
        check_count -= 1
        #print(f"error : {ticker['market']} / {check_count}")
        df = pyupbit.get_ohlcv(ticker['market'], interval=interval, count=checkCount)
        await asyncio.sleep(0.1)

    #요청한 수만큼 존재하지 않다면 이 이상의 계산은 의미가 없습니다. 리턴 처리 하자.
    if len(df) < checkCount:
        return

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
        

async def CheckList(list_ticker, interval, checkCount):
    count = 0
    for ticker in list_ticker:
        await CheckTicker(ticker, list_spike, interval, checkCount)
        count += 1
        await asyncio.sleep(0.1)

        if is_test and 50 <= count:
            break
    
    if(0 < len(list_spike) ):
        print_msg(f"spike coin find!! : {list_spike}")

async def StartCheck(interval, checkCount):

    MakeTickerList(list_ticker, list_ticker_warning)

    task1 = asyncio.create_task(CheckList(list_ticker, interval, checkCount))
    task2 = asyncio.create_task(CheckList(list_ticker, "minutes10", checkCount))
    
    await task1
    await task2

def Main(interval, checkCount):
    #print(f"interval:{interval}, checkCount:{checkCount}")
    asyncio.run(StartCheck(interval, checkCount))

print_msg(f"check ticker start")
#schedule.every(3).minutes.do(Main, interval="minutes3", checkCount=200)
#schedule.every(10).minutes.do(Main, interval="minutes10", checkCount=200)
schedule.every(10).seconds.do(Main, interval="minutes3", checkCount=200)
#schedule.every(10).seconds.do(Main, interval="minutes10", checkCount=200)

#schedule.every(1).seconds.do(Main, interval="minutes3", checkCount=200)
#schedule.every(2).seconds.do(Main, interval="minutes1", checkCount=100)

while True:
    schedule.run_pending()
    time.sleep(1)