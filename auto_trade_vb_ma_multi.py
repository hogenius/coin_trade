"""

변동성 돌파 전략(Volatility Breakout)
+
이동평균선 전략(Moving Average Line)
+
비율에 따른 선택적 코인 매수 매도

"""

import time
import pyupbit
import datetime
import find_best_k
import pandas
import msg_discord
from config import ConfigInfo
config = ConfigInfo()
is_test = True
list_coin_info = []


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
    if is_test:
        msg = 'TestMode:' + msg
    print(msg)
    if withDiscord:
        msg_discord.send(msg)

def make_coin_list(list):

    list.clear()

    for i in range(len(config.list_coin)):
        data = config.list_coin[i]
        list.append({'name':data['name'], 'rate':data['rate'], 'best_k':find_best_k.GetBestK(data['name']),'is_buy':False, 'krw_avaiable':-1})
    check_available_krw(list)
    print_msg(f"make_coin_list : {list}")

def check_available_krw(list):
    #보유하고 있는 현금을 기준으로 비율을 정산합니다.

    krw_total = get_balance("KRW")

    is_need_noti = False
    list_rate = []

    print(f"check_available_krw krw_total: {krw_total}")
    rate_total = 0
    for i in range(len(list)):    
        if list[i]['is_buy'] == True:
            continue
        rate_total += list[i]['rate']

    for i in range(len(list)):    
        if list[i]['is_buy'] == True:
            if 0 < list[i]['krw_avaiable']:
                list_rate.append({'name':list[i]['name'], 'krw_before':list[i]['krw_avaiable'], 'krw_after':0})
                list[i]['krw_avaiable'] = 0
                is_need_noti = True

            continue

        krw_change = krw_total * (list[i]['rate'] / rate_total)
        
        if list[i]['krw_avaiable'] != -1 and list[i]['krw_avaiable'] != krw_change:
            list_rate.append({'name':list[i]['name'], 'krw_before':list[i]['krw_avaiable'], 'krw_after':krw_change})
            is_need_noti = True

        list[i]['krw_avaiable'] = krw_change
        
    if is_need_noti:
        print_msg(f"available_krw change : {list_rate}")


# login
upbit = pyupbit.Upbit(config.access,config.secret)
print_msg(f"autotrade start")
make_coin_list(list_coin_info)

# 자동매매 시작
while True:
    try:
        check_available_krw(list_coin_info)

        is_need_refesh = False

        for i in range(len(list_coin_info)):

            now = datetime.datetime.now()
            start_time = get_start_time("KRW-BTC") # 09:00 대표시간으로 BTC를 사용합니다.
            end_time = start_time + datetime.timedelta(days=1) # 09:00 + 1일
            coin_name = list_coin_info[i]['name']

            # 9시부터 < 현재 < 담날08:59:50까지 돌도록
            if start_time < now < end_time - datetime.timedelta(seconds=config.loop_sec*3):

                #매수 프로세스
                if list_coin_info[i]['is_buy'] == True:
                        continue

                #이동평균선을 구한다.
                df = pyupbit.get_ohlcv(coin_name, count=config.ma_3)
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

                #1번 이동평균이 2번 이동평균선보다 이상이면 정배열로 간주한다.
                is_regulat_arr = (data_ma_2 < data_ma_1)
                print(f"is_regulat_arr : {is_regulat_arr}")

                target_price = get_target_price(coin_name, list_coin_info[i]['best_k'])
                current_price = get_current_price(coin_name)

                #이동평균선 정배열이면서 best_k에 의해 변동성이 돌파했다면?! 매수 가즈아
                if is_regulat_arr and target_price < current_price:
                    
                    krw_total = get_balance("KRW")
                    krw = list_coin_info[i]['krw_avaiable']

                    #보완처리. 비율료 계산되었던 현금가용액이 실제 보유현금액보다 크다?
                    if krw_total < krw:
                        krw = krw_total

                    if krw > 5000:
                        buy_krw = krw*0.9995
                        if is_test == False:
                            upbit.buy_market_order(coin_name, buy_krw)
                        print_msg(f"autotrade buy_market_order {coin_name}:{buy_krw}")

                        #매수한것으로 표기. 하루에 반복적으로 구매 하지 않습니다.
                        #하루가 지나서 전량 매도가 되기전에 사용자 임의로 매도를 할수 있도록 말이죠.
                        list_coin_info[i]['is_buy'] = True

                        #print(f"after buy list_coin_info : {list_coin_info}")

            else:
                #전량 매도.
                coin_name_pure = coin_name.replace('KRW-', '')
                #print(f"coin {coin_name} -> {coin_name_pure}")
                coin_balance = get_balance(coin_name_pure)
                if coin_balance > 0.00008:
                    sell_coin = coin_balance*0.9995
                    if is_test == False:
                        upbit.sell_market_order(coin_name, sell_coin)
                    print_msg(f"autotrade sell_market_order {coin_name}:{sell_coin}")
                
                is_need_refesh = True

        #초기화 구문.
        if is_need_refesh:    
            print_msg(f"autotrade refresh")
            make_coin_list(list_coin_info)

        #test = 1
        #print(f"autotrade check")

        #best_k = find_best_k.GetBestK()
        #print(f"autotrade check best k {best_k}")
        time.sleep(config.loop_sec)
    except Exception as e:
        print(e)
        time.sleep(config.loop_sec)