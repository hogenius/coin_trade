"""

변동성 돌파 전략(Volatility Breakout)
+
이동평균선 전략(Moving Average Line)
+
비율에 따른 선택적 코인 매수 매도

"""
import asyncio
import schedule
import time
import pyupbit
import datetime
import find_best_k
import pandas
import msg_discord as MsgService
#import msg_telegram as MsgService
import check_ticker
from config import ConfigInfo
config = ConfigInfo.Instance()
is_test = False
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

def get_revenue_rate(balances, ticker):
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

def print_msg(msg, withNotification=True):
    if is_test:
        msg = 'TestMode:' + msg
    print(msg)
    if withNotification:
        MsgService.send(msg)

def make_coin_list(list):

    list.clear()

    for i in range(len(config.list_coin)):
        data = config.list_coin[i]
        list.append({
            'name':data['name'], 
            'rate':data['rate'], 
            'rate_profit':data['rate_profit'], 
            'rate_stop_loss':data['rate_stop_loss'], 
            'best_k':find_best_k.GetBestK(data['name']),
            'is_buy':False, 
            'is_sell':False, 
            'krw_avaiable':-1})
    check_available_krw(list)
    print_msg(f"make_coin_list : {list}")


def check_available_krw(list):
    #보유하고 있는 현금을 기준으로 비율을 정산합니다.

    #krw_total = get_balance("KRW")

    #이미 보유하고 있는 코인이면 구매한것으로 간주합니다.
    balances = upbit.get_balances()
    for b in balances:

        if b['currency'] == "KRW" and (b['balance'] is not None) :
            krw_total = float(b['balance'])
            continue

        for i in range(len(list)):    
            if b['currency'] == list[i]['name'].replace('KRW-', '') and (b['balance'] is not None) and 0.01 < float(b['balance']) :
                list[i]['is_buy'] = True

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

def coin_process():

    # 자동매매 시작
    try:
        check_available_krw(list_coin_info)

        is_need_refesh = False
        balances = upbit.get_balances()

        now = datetime.datetime.now()
        end_time = now.replace(hour=7, minute=0, second=0, microsecond=0)
        start_time = end_time - datetime.timedelta(seconds=config.loop_sec*3)

        start_time_wait = end_time
        end_time_wait = now.replace(hour=9, minute=0, second=0, microsecond=0)

        for i in range(len(list_coin_info)):

            coin_name = list_coin_info[i]['name']

            #KST 06:57 ~ 07:00동안은 매도프로세스를 진행합니다.
            if start_time < now < end_time:
                #매도 프로세스 시작.
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
            elif start_time_wait <= now <= end_time_wait:
                #do nothing..
                continue
            else:
                #매수 프로세스 체크 시작.
                if list_coin_info[i]['is_buy'] == True:

                    #매수도 했었고 그에 이어서 매도도 했었다면 더이상 할게 없다.
                    if list_coin_info[i]['is_sell'] == True:
                        continue

                    rate_profit = list_coin_info[i]['rate_profit']
                    rate_stop_loss = list_coin_info[i]['rate_stop_loss']
                    if 0 < rate_profit or rate_stop_loss < 0:

                        #매수한 상태이니 이제 수익률을 계산합니다.
                        revenue_rate = get_revenue_rate(balances, list_coin_info[i]['name'])

                        is_need_sell = False
                        if 0 < rate_profit and rate_profit <= revenue_rate:
                            #익절하자!!
                            is_need_sell = True
                        elif rate_stop_loss < 0 and revenue_rate <= rate_stop_loss:
                            #손절하자!!
                            is_need_sell = True

                        if is_need_sell:
                            #전량 매도.
                            coin_name_pure = coin_name.replace('KRW-', '')
                            coin_balance = get_balance(coin_name_pure)
                            if coin_balance > 0.00008:
                                sell_coin = coin_balance*0.9995
                                if is_test == False:
                                    upbit.sell_market_order(coin_name, sell_coin)
                                print_msg(f"autotrade sell_market_order {coin_name}:{sell_coin}")
                                list_coin_info[i]['is_sell'] = True

                else:
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
                    #print(f"is_regulat_arr : {is_regulat_arr}")

                    target_price = get_target_price(coin_name, list_coin_info[i]['best_k'])
                    current_price = get_current_price(coin_name)

                    #이동평균선 정배열이면서 best_k에 의해 변동성이 돌파했다면?! 매수 가즈아
                    if is_regulat_arr and target_price < current_price:
                        
                        print(f"is_regulat_arr && target_price:{target_price} < current_price:{current_price}")
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
                            print_msg(f"autotrade not enough money to buy_market_order {coin_name}. krw:{krw}")

        #초기화 구문.
        if is_need_refesh:    
            print_msg(f"autotrade refresh")
            make_coin_list(list_coin_info)

        #test = 1
        #print(f"autotrade check")

        #best_k = find_best_k.GetBestK()
        #print(f"autotrade check best k {best_k}")
    except Exception as e:
        print(e)

async def main_async():
    print_msg(f"auto trade start")
    make_coin_list(list_coin_info)
    while True:
        coin_process()
        await asyncio.sleep(config.loop_sec)
        
if __name__ == '__main__':

    upbit = pyupbit.Upbit(config.access,config.secret)

    loop = asyncio.get_event_loop()
    loop.create_task(main_async())
    #loop.create_task(msg_async())
    #loop.create_task(check_async())
    loop.run_forever()