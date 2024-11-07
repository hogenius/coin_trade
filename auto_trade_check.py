"""

변동성 돌파 전략(Volatility Breakout)
+
이동평균선 전략(Moving Average Line)
+
비율에 따른 선택적 코인 매수 매도

"""
import asyncio
import pyupbit
import datetime
import find_best_k
import pandas
import json
from msg_telegram import Messaging
from config import ConfigInfo
from event import EventManager
from exchange_rate import ExchangeRater
from simple_common.simpledata import SimpleData
from simple_common.simpledata import TableType
from simple_common.Logging import SimpleLogger

class CoinTrade:

    def __init__(self, name, upbit, isTest):
        self.is_waiting = False
        self.is_pause = False
        self.is_test = isTest
        self.upbit = upbit
        self.list_coin_info = []
        self.config = ConfigInfo.Instance()
        self.simple_data = SimpleData(ConfigInfo.Instance().db_path)
        #EventManager.Instance().Regist("BUY_COIN_LIST", self.BuyCoinList)
        # EventManager.Instance().Regist("REFRESH_COIN_LIST", self.RefreshCoinList)
        # EventManager.Instance().Regist("CHECK_COIN_LIST", self.CheckCoinList)
        # EventManager.Instance().Regist("RELOAD_CONFIG", self.ReloadConfing)
        # EventManager.Instance().Regist("SAFE_MODE", self.SetSafeMode)
        # EventManager.Instance().Regist("NORMAL_MODE", self.SetNormalMode)
        # EventManager.Instance().Regist("PAUSE", self.SetPause)
        # EventManager.Instance().Regist("RESUME", self.SetResume)
        self.logging = SimpleLogger(name="coin_trade", log_file="coin_trade.log")

    def SetResume(self):
        self.is_pause = False
        self.print_msg(f"set resume mode. self.is_pause : {self.is_pause}")

    def SetPause(self):
        self.is_pause = True
        self.print_msg(f"set pause mode. self.is_pause : {self.is_pause}")

    def SetSafeMode(self):
        for i in range(len(self.list_coin_info)):
            if self.list_coin_info[i]['rate_profit'] < 1.0:
                self.list_coin_info[i]['rate_profit'] = 1.0
            self.list_coin_info[i]['check_buy_count'] = self.list_coin_info[i]['check_buy_count_origin'] * 2
        self.print_msg("set safe mode coin list")
        self.print_msg(self.list_coin_info)

    def SetNormalMode(self):
        for i in range(len(self.list_coin_info)):
            self.list_coin_info[i]['rate_profit'] = self.list_coin_info[i]['rate_profit_origin']
            self.list_coin_info[i]['check_buy_count'] = self.list_coin_info[i]['check_buy_count_origin']
        self.print_msg("set normal mode coin list")
        self.print_msg(self.list_coin_info)

    def ReloadConfing(self):
        self.config.ReloadAll()

    def CheckCoinList(self):
        self.coin_process(True)

    def RefreshCoinList(self):
        self.make_coin_list(self.list_coin_info)

    # def BuyCoinList(self):

        # if len(listCoin) <= 0:
        #     return
        
        # # 'name':ticker, 
        # # 'stdev_volume_before':stdev_volume_before,
        # # 'stdev_volume':stdev_volume
        
        # listCoin.sort(key=lambda x: x['stdev_volume'], reverse=True)
        # print(f"(TEST)BuyCoinList BuyCoin : {listCoin}")
        # #아직은 작업중이니 이벤트가 들어와도 진행을 멈춥니다.
        # return
        # for i in range(len(self.list_coin_info)):
        #     coin_info = self.list_coin_info[i]
        #     if coin_info['name'] != "CHECK":
        #         continue
        #     else:
        #         coin_info['name'] = listCoin[0]['name']
        #         self.coin_buy(coin_info)

    async def InitRoutine(self):
        self.print_msg(f"auto trade start")
        self.make_coin_list(self.list_coin_info)
        while True:
            self.coin_process(False)
            if self.is_test:
                print("InitRoutine")
            await asyncio.sleep(ConfigInfo.Instance().loop_sec)

    async def InitPollingRoutine(self):

        while True:
            list_check = self.simple_data.load_strings(TableType.Check)
            if self.is_test:
                print(f"InitPollingRoutine : {list_check}");
            for check_name in list_check:
                if hasattr(self, check_name):
                    method = getattr(self, check_name)
                    method()
            
            await asyncio.sleep(ConfigInfo.Instance().polling_sec)

    def get_target_price(self, ticker, k):
        """변동성 돌파 전략으로 매수 목표가 조회"""
        df = pyupbit.get_ohlcv(ticker, interval="day", count=2)
        target_price = df.iloc[0]['close'] + (df.iloc[0]['high'] - df.iloc[0]['low']) * k
        return target_price

    def get_start_time(self, ticker):
        """시작 시간 조회"""
        df = pyupbit.get_ohlcv(ticker, interval="day", count=1)
        start_time = df.index[0]
        return start_time

    def get_balance(self, ticker):
        """잔고 조회"""
        balances = self.upbit.get_balances()
        for b in balances:
            if b['currency'] == ticker:
                if b['balance'] is not None:
                    return float(b['balance'])
                else:
                    return 0
        return 0

    def get_current_price(self, ticker):
        """현재가 조회"""
        return pyupbit.get_orderbook(ticker=ticker)["orderbook_units"][0]["ask_price"]

    def get_revenue_rate(self, balances, ticker):
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

    def print_msg(self, data, withNotification=True):

        msg = ""
        if type(data) is not str:            
            msg = json.dumps(data, indent=4)
        else:
            msg = data

        print(msg)
        self.logging.log(msg)

        if withNotification:
            #Messaging.Instance().Send(msg)
            now = datetime.datetime.now()
            if self.is_test:
                message = f"TestMode\n[{now.strftime('%Y-%m-%d %H:%M:%S')}]\n{str(msg)}"
            else:
                message = f"[{now.strftime('%Y-%m-%d %H:%M:%S')}]\n{str(msg)}"

            self.simple_data.add_string(TableType.Msg, message)

    def make_coin_list(self, list):

        list.clear()

        for i in range(len(self.config.list_coin)):
            data = self.config.list_coin[i]
            list.append({
                'name':data['name'], 
                'rate':data['rate'], 
                'rate_profit':data['rate_profit'], 
                'rate_profit_origin':data['rate_profit'], 
                'rate_stop_loss':data['rate_stop_loss'], 
                'best_k':find_best_k.GetBestK(data['name']),
                'is_buy':False, 
                'is_sell':False, 
                'krw_avaiable':-1,
                'check_sell':data['check_sell'],
                'check_buy':data['check_buy'],
                'check_buy_count':data['check_buy_count'],
                'check_buy_count_origin':data['check_buy_count'],
                'is_sell_routine':data['is_sell_routine'],
                'is_repeat_buy_routine':data['is_repeat_buy_routine'],
                })
        self.check_available_krw(list)
        self.print_msg("make_coin_list")
        self.print_msg(list)

    def check_available_krw(self, list, isForce=False):
        #보유하고 있는 현금을 기준으로 비율을 정산합니다.

        #krw_total = get_balance("KRW")

        #이미 보유하고 있는 코인이면 구매한것으로 간주합니다.
        balances = self.upbit.get_balances()
        #print(f"check_available_krw : {balances}")
        for b in balances:

            if b['currency'] == "KRW" and (b['balance'] is not None) :
                krw_total = float(b['balance'])
                continue

            for i in range(len(list)):    
                if b['currency'] == list[i]['name'].replace('KRW-', '') and (b['balance'] is not None):
                    cost_total_past = float(b['balance']) * float(b['avg_buy_price'])
                    #print(f"{list[i]['name']} : cost_total_past : {cost_total_past}")
                    if 5000 < cost_total_past :
                        list[i]['is_buy'] = True
                        list[i]['buy_price'] = cost_total_past

        is_need_noti = False
        list_rate = []


        self.print_msg(f"check_available_krw krw_total: {krw_total}", isForce)
        rate_total = 0
        for i in range(len(list)):    
            if list[i]['is_buy'] == True:
                continue
            rate_total += list[i]['rate']

        for i in range(len(list)):    

            if list[i]['rate'] <= 0:
                continue

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
            self.print_msg("available_krw change")
            self.print_msg(list_rate)

    def coin_buy(self, coinInfo):
        
        krw_total = self.get_balance("KRW")
        krw = coinInfo['krw_avaiable']

        #보완처리. 비율료 계산되었던 현금가용액이 실제 보유현금액보다 크다?
        if krw_total < krw:
            krw = krw_total

        if krw > 5000:
            buy_krw = krw*0.9995
            if self.is_test == False:
                self.upbit.buy_market_order(coinInfo['name'], buy_krw)

            self.print_msg(f"[BUY] {coinInfo['name']}:{buy_krw:,.2f}")

            #매수한것으로 표기. 하루에 반복적으로 구매 하지 않습니다.
            #하루가 지나서 전량 매도가 되기전에 사용자 임의로 매도를 할수 있도록 말이죠.

            coinInfo['is_buy'] = True
            coinInfo['buy_price'] = buy_krw

            #print(f"after buy list_coin_info : {list_coin_info}")
        else:
            self.print_msg(f"[BUY ERROR] not enough money to buy_market_order {coinInfo['name']}. krw:{krw:,.2f}")

    def coin_sell(self, coinInfo):
        
        result = False
        coin_name_pure = coinInfo['name'].replace('KRW-', '')
        coin_balance = self.get_balance(coin_name_pure)
        if coin_balance > 0.00008:
            sell_coin = coin_balance*0.9995
            if self.is_test == False:
                self.upbit.sell_market_order(coinInfo['name'], sell_coin)
            result = True
            sell_krw = self.get_current_price(coinInfo['name']) * sell_coin
            if "buy_price" in coinInfo:
                margin_krw = sell_krw - coinInfo['buy_price']
                del coinInfo['buy_price']
                self.print_msg(f"[SELL] {coinInfo['name']}:{sell_coin}\nsell_krw:{sell_krw:,.2f}\nmargin_krw:{margin_krw:,.2f}")
            else:
                self.print_msg(f"[SELL] {coinInfo['name']}:{sell_coin}\nsell_krw:{sell_krw:,.2f}\nmargin_krw:unknown")
            coinInfo['is_sell'] = True
            coinInfo['sell_price'] = sell_krw
        
        return result
       
    #이동평균선을 구한다.
    def check_buy_ma(self, coin_info, balances, isForce):
        coin_name = coin_info['name']
        df = pyupbit.get_ohlcv(coin_name, count=self.config.ma_3)
        df['MA_1'] = df['close'].rolling(self.config.ma_1).mean()
        df['MA_2'] = df['close'].rolling(self.config.ma_2).mean()
        #df['MA_3'] = df['close'].rolling(config.ma_3).mean()
        pandas.set_option('display.float_format', lambda x: '%.1f' % x)

        last_data = df.iloc[(len(df)-1)]
        data_ma_1 = last_data['MA_1']
        data_ma_2 = last_data['MA_2']
        #data_ma_3 = last_data['MA_3']

        #print(f"{config.ma_1}ma:{data_ma_1}, {config.ma_2}ma:{data_ma_2}, {config.ma_3}ma:{data_ma_3}")
        #is_regulat_arr = (data_ma_3 < data_ma_2 < data_ma_1)

        #1번 이동평균이 2번 이동평균선보다 이상이면 정배열로 간주한다.
        is_regulat_arr = (data_ma_2 < data_ma_1)
        self.print_msg(f"{coin_name} - check_ma: {self.config.ma_2}ma:{data_ma_2} < {self.config.ma_1}ma:{data_ma_1} = {is_regulat_arr}", isForce)

        return is_regulat_arr

     #변동성 돌파를 구한다.
    def check_buy_vb(self, coin_info, balances, isForce):
        coin_name = coin_info['name']
        bestK = coin_info['best_k']
        target_price = self.get_target_price(coin_name, bestK)
        current_price = self.get_current_price(coin_name)

        is_over_target_price = target_price < current_price
        self.print_msg(f"{coin_name} - check_vb: target:{target_price:,.2f} < current:{current_price:,.2f} = {is_over_target_price}", isForce)

        return is_over_target_price
    
    #환율 기준으로 체크한다.
    def check_buy_exchange_rate(self, coin_info, balances, isForce):
        coin_name = coin_info['name']
        rate_usd = ExchangeRater.Instance().GetUSD();
        current_price = self.get_current_price(coin_name)

        is_low_price_state = current_price < rate_usd
        self.print_msg(f"{coin_name} - check_exchange_rate: current:{current_price:,.2f} < e_rate_usd:{rate_usd:,.2f} = {is_low_price_state}", isForce)

        return is_low_price_state
    
    #무조건 판매 시간인지 체크한다.
    def check_sell_time(self, coin_info, balances, isForce):
        now = datetime.datetime.now()
        end_time = now.replace(hour=7, minute=0, second=0, microsecond=0)
        start_time = end_time - datetime.timedelta(seconds=self.config.loop_sec*3)

        #매도 시간 KST 06:57 ~ 07:00
        return start_time < now < end_time
    
    #수익비율 조건 상태인지 체크한다.
    def check_sell_profit(self, coin_info, balances, isForce):
        coin_name = coin_info['name']
        rate_profit = coin_info['rate_profit']
        result = False
        if 0 < rate_profit:
            #매수한 상태이니 이제 수익률을 계산합니다.
            revenue_rate = self.get_revenue_rate(balances, coin_name)
            result = rate_profit <= revenue_rate  
        self.print_msg(f"{coin_name} - check sell: rate_profit({rate_profit}) <= revenue_rate({revenue_rate}) = {result}", isForce)
        return result

    #손해비율 조건 상태인지 체크한다.
    def check_sell_loss(self, coin_info, balances, isForce):
        coin_name = coin_info['name']
        rate_stop_loss = coin_info['rate_stop_loss']
        result = False
        if rate_stop_loss < 0:
            #매수한 상태이니 이제 수익률을 계산합니다.
            revenue_rate = self.get_revenue_rate(balances, coin_name)
            result = revenue_rate <= rate_stop_loss

        self.print_msg(f"{coin_name} - check sell: revenue_rate({revenue_rate}) <= rate_stop_loss({rate_stop_loss}) = {result}", isForce)
        return result
    
    def coin_process_sell(self):
        if self.is_pause:
            return False
        
        #매도 프로세스 시작.
        for i in range(len(self.list_coin_info)):
            #전량 매도.
            is_sell_routine = self.list_coin_info[i]['is_sell_routine']
            #list_check = self.list_coin_info[i]['check']
            if is_sell_routine:
                self.coin_sell(self.list_coin_info[i])

        return True
    
    def coin_process_buy_check(self, isForce):

        balances = self.upbit.get_balances()
        
        #매수 프로세스 시작.
        for i in range(len(self.list_coin_info)):
            coin_name = self.list_coin_info[i]['name']
            best_k = self.list_coin_info[i]['best_k']

            if self.list_coin_info[i]['is_buy'] == True:

                #매수도 했었고 그에 이어서 매도도 했었다면 더이상 할게 없다.
                if self.list_coin_info[i]['is_sell'] == True:
                    continue

                if self.is_pause:
                    continue

                rate_profit = self.list_coin_info[i]['rate_profit']
                rate_stop_loss = self.list_coin_info[i]['rate_stop_loss']
                is_check_profit = 0 < rate_profit
                is_check_stop_loss = rate_stop_loss < 0
                if is_check_profit or is_check_stop_loss:

                    #매수한 상태이니 이제 수익률을 계산합니다.
                    revenue_rate = self.get_revenue_rate(balances, self.list_coin_info[i]['name'])

                    is_profit_sell = is_check_profit and rate_profit <= revenue_rate
                    is_loss_sell = is_check_stop_loss and revenue_rate <= rate_stop_loss

                    if is_check_profit:
                        #익절
                        self.print_msg(f"{coin_name} - check sell: rate_profit({rate_profit}) <= revenue_rate({revenue_rate}) = {is_profit_sell}", isForce)

                    if is_check_stop_loss:
                        #손절
                        self.print_msg(f"{coin_name} - check sell: revenue_rate({revenue_rate}) <= rate_stop_loss({rate_stop_loss}) = {is_loss_sell}", isForce)

                    if is_profit_sell or is_loss_sell:
                        #전량 매도.
                        self.coin_sell(self.list_coin_info[i])

                        if self.list_coin_info[i]['is_repeat_buy_routine'] == True:
                             self.list_coin_info[i]['is_buy'] = False
                             self.list_coin_info[i]['is_sell'] = False

                else:
                    self.print_msg(f"{coin_name} - check sell: do nothing..", isForce)

            else:
                
                check_complete_count = 0
                list_check = self.list_coin_info[i]['check']
                for j in range(len(list_check)):
                    check_name = list_check[j]
                    if hasattr(self, check_name):
                        method = getattr(self, check_name)
                        if method(self.list_coin_info[i], best_k, isForce) == True:
                            check_complete_count+=1

                if self.is_pause:
                    continue
                
                # #이동평균선을 구한다.
                # is_regulat_arr = self.check_ma(coin_name, isForce)
                # #변동성 돌파를 구한다.
                # is_over_target_price = self.check_vb(coin_name, self.list_coin_info[i]['best_k'], isForce)
                
                #이동평균선 정배열이면서 best_k에 의해 변동성이 돌파했다면?! 매수 가즈아
                #if is_regulat_arr and is_over_target_price:
                check_count = self.list_coin_info[i]['check_buy_count']
                if len(list_check) <= check_complete_count:

                    if check_count <= 0:
                        #매수합니다.
                        #print(f"is_regulat_arr && target_price:{target_price} < current_price:{current_price}")
                        self.coin_buy(self.list_coin_info[i])
                    else:
                        #체크완료 카운트를 하나 뺍니다.
                        set_check_count = check_count - 1
                        self.list_coin_info[i]['check_buy_count'] = set_check_count
                        self.print_msg(f"[CHECK BUY] {self.list_coin_info[i]['name']}.  remain check count:{set_check_count}")

                elif check_count != self.list_coin_info[i]['check_buy_count_origin']:
                    self.list_coin_info[i]['check_buy_count'] = self.list_coin_info[i]['check_buy_count_origin']
                    self.print_msg(f"[CHECK RESET] {self.list_coin_info[i]['name']}")

        return False

    def coin_process(self, isForce):

        # 자동매매 시작
        try:
            is_need_refesh = False
            
            now = datetime.datetime.now()
            end_time = now.replace(hour=7, minute=0, second=0, microsecond=0)
            start_time = end_time - datetime.timedelta(seconds=self.config.loop_sec*3)

            start_time_wait = end_time
            end_time_wait = now.replace(hour=9, minute=0, second=0, microsecond=0)

            if start_time < now < end_time:
                #매도 시간 KST 06:57 ~ 07:00
                self.check_available_krw(self.list_coin_info, isForce)
                is_need_refesh = self.coin_process_sell()
            elif start_time_wait <= now <= end_time_wait:
                #쉬는 시간.ㅎㅋ KST 07:00 ~ 09:00
                is_need_refesh = False
                self.is_waiting = True
            elif self.is_waiting == True:
                #쉬는 시간끝나으면 리프레쉬 해줍니다.
                self.is_waiting = False
                is_need_refesh = True
            else:
                #매수 체크 시간
                self.check_available_krw(self.list_coin_info, isForce)
                is_need_refesh = self.coin_process_buy_check(isForce)
            
            #초기화 구문.
            if is_need_refesh:    
                self.print_msg("autotrade refresh")
                self.make_coin_list(self.list_coin_info)

            #test = 1
            #print(f"autotrade check")

            #best_k = find_best_k.GetBestK()
            #print(f"autotrade check best k {best_k}")
        except Exception as e:
            print(e)


    def coin_main_loop(self, isForce):
        
        try:
            if self.is_pause:
                return
         
            balances = self.upbit.get_balances()

            count_re_process = 0
            count_sell_process = 0
            count_buy_process = 0

            for i in range(len(self.list_coin_info)):
                coin_info = self.list_coin_info[i]
                if coin_info['is_sell'] == True:
                    #한번 매수했다가 매도까지 했었습니다.

                    
                    if coin_info['is_repeat_buy_routine'] == True:
                        #다시 매수 프로세스를 활성화하는 옵션이라면 초기화.
                        coin_info['is_buy'] = False
                        coin_info['is_sell'] = False
                        count_re_process += 1
                    else:
                        #시간되면 무조건 매도 조건이 붙어있는경우.
                        list_check = coin_info['check_sell']
                        is_have_check_sell_time = False
                        for j in range(len(list_check)):
                            check_name = list_check[j]
                            if check_name == "check_sell_time":
                                is_have_check_sell_time = True
                                break
                        if is_have_check_sell_time:
                            now = datetime.datetime.now()
                            end_time_wait = now.replace(hour=9, minute=0, second=0, microsecond=0)
                            if end_time_wait <= now:
                                coin_info['is_buy'] = False
                                coin_info['is_sell'] = False
                                coin_info['krw_avaiable'] = -1
                                coin_info['check_buy_count'] = coin_info['check_buy_count_origin']
                                coin_info['best_k'] = find_best_k.GetBestK(coin_info['name'])
                                count_re_process += 1
                        
                else:
                    #매도 혹은 매수 프로세스를 해야합니다.
                    if coin_info['is_buy'] == True:
                        #매수를 했었다면 매도 체크 프로세스를 실행.

                        #체크 메서드를 루프로 실행해서 체크한다.
                        check_complete_count = 0
                        list_check = coin_info['check_sell']
                        for j in range(len(list_check)):
                            check_name = list_check[j]
                            if hasattr(self, check_name):
                                method = getattr(self, check_name)
                                if method(coin_info, balances, isForce) == True:
                                    check_complete_count+=1
                        
                        #매도 체크 조건을 모두 만족했다면 매도처리!            
                        if(len(list_check) <= check_complete_count):
                            self.coin_sell(coin_info)
                            count_sell_process+=1

                    else:
                        #매수가 가능한지 체크 프로세스를 실행.

                        #체크 메서드를 루프로 실행해서 체크한다.
                        check_complete_count = 0
                        list_check = coin_info['check_buy']
                        for j in range(len(list_check)):
                            check_name = list_check[j]
                            if hasattr(self, check_name):
                                method = getattr(self, check_name)
                                if method(coin_info, balances, isForce) == True:
                                    check_complete_count+=1

                        #매수 체크 조건을 모두 만족했다!    
                        if(len(list_check) <= check_complete_count):
                            
                            #매수 카운팅을 체크합니다.
                            check_count = coin_info['check_buy_count']
                            if check_count <= 0:
                                    #매수합니다.
                                    #print(f"is_regulat_arr && target_price:{target_price} < current_price:{current_price}")
                                    self.coin_buy(coin_info)
                                    count_buy_process+=1
                            else:
                                #체크완료 카운트를 하나 뺍니다.
                                set_check_count = check_count - 1
                                coin_info['check_buy_count'] = set_check_count
                                self.print_msg(f"[CHECK BUY] {coin_info['name']}.  remain check count:{set_check_count}")

                        #매수 체크 조건을 불만족했다면 check_buy_count 초기화.
                        elif check_count != coin_info['check_buy_count_origin']:
                                coin_info['check_buy_count'] = coin_info['check_buy_count_origin']
                                self.print_msg(f"[CHECK RESET] {coin_info['name']}")

            if 0 < count_re_process or 0 < count_sell_process or 0 < count_buy_process:
                self.check_available_krw(self.list_coin_info, isForce)
        except Exception as e:
            print(e)
            self.print_msg(f"[ERROR] {e}")

            
