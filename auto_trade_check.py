"""

변동성 돌파 전략(Volatility Breakout)
+
이동평균선 전략(Moving Average Line)
+
비율에 따른 선택적 코인 매수 매도

"""
import time
import traceback
import re
import asyncio
from enum import Enum
import os
import pyupbit
import datetime
import find_best_k
import pandas
import json
import sys
import importlib.util
import importlib
from msg_telegram import Messaging
from config import ConfigInfo
from event import EventManager
from simple_common.simpledata import SimpleData
from simple_common.simpledata import TableType
from simple_common.Logging import SimpleLogger

class TypeCondition(Enum):
    Required = "Required"   #필수 조건
    Optional = "Optional"   #추가 조건

class CoinTrade:

    def __init__(self, name, upbit, isTest):
        self.last_checked_date = None  # 이전 날짜를 저장할 변수
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

    def SetResume(self, *args):
        self.is_pause = False
        self.print_msg(f"set resume mode. self.is_pause : {self.is_pause}")

    def SetPause(self, *args):
        self.is_pause = True
        self.print_msg(f"set pause mode. self.is_pause : {self.is_pause}")

    def SetSafeMode(self, *args):
        for i in range(len(self.list_coin_info)):
            if self.list_coin_info[i]['rate_profit'] < 1.0:
                self.list_coin_info[i]['rate_profit'] = 1.0
            self.list_coin_info[i]['is_check_buy_count'] = True
            self.list_coin_info[i]['check_buy_count'] = self.list_coin_info[i]['check_buy_count_origin'] * 2
        self.print_msg("set safe mode coin list")
        self.print_msg(self.list_coin_info)

    def SetNormalMode(self, *args):
        for i in range(len(self.list_coin_info)):
            self.list_coin_info[i]['rate_profit'] = self.list_coin_info[i]['rate_profit_origin']
            self.list_coin_info[i]['is_check_buy_count'] = True
            self.list_coin_info[i]['check_buy_count'] = self.list_coin_info[i]['check_buy_count_origin']
        self.print_msg("set normal mode coin list")
        self.print_msg(self.list_coin_info)

    def SetAttackMode(self, *args):
        for i in range(len(self.list_coin_info)):
            self.list_coin_info[i]['rate_profit'] = 0.0
            self.list_coin_info[i]['check_buy_count'] = 0
            self.list_coin_info[i]['is_check_buy_count'] = False
        self.print_msg("set attack mode coin list")
        self.print_msg(self.list_coin_info)

    def ReloadConfing(self, *args):
        self.config.ReloadAll()

    def CheckCoinList(self, *args):
        self.coin_main_loop(True)

    def RefreshCoinList(self, *args):
        self.make_coin_list(self.list_coin_info)

    def ShowStatus(self, *args):
        for i in range(len(self.list_coin_info)):
            coin_info = self.list_coin_info[i]
            self.print_msg(coin_info)

    def cmd(self, *args):
        self.print_msg(f"cmd - {args}")

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
            self.coin_main_loop(False)
            if self.is_test:
                print("InitRoutine")
            await asyncio.sleep(ConfigInfo.Instance().loop_sec)

    async def InitPollingRoutine(self):

        while True:
            list_check = self.simple_data.load_strings(TableType.Check)
            if self.is_test:
                print(f"InitPollingRoutine : {list_check}")
            for check_name in list_check:
                method_name = check_name
                args = []
                if "/" in check_name or "_" in check_name:
                    args_list = re.split(r"[/_]", check_name)
                    method_name, *args = args_list
                    
                if hasattr(self, method_name):
                    method = getattr(self, method_name)
                    try:
                        method(*args)
                    except Exception as e:
                        print(f"Error calling method '{method_name}': {e}")
            
            await asyncio.sleep(ConfigInfo.Instance().polling_sec)

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
                'is_check_buy_count':data['is_check_buy_count'],
                'is_repeat_buy_routine':data['is_repeat_buy_routine'],
                })
        self.check_available_krw(list)
        self.print_msg("make_coin_list")
        #self.print_msg(list)
        for i in range(len(self.list_coin_info)):
            coin_info = self.list_coin_info[i]
            self.print_msg(f"[SET]{coin_info['name']}/rate:{coin_info['rate']}/krw:{coin_info['krw_avaiable']}/best_k:{coin_info['best_k']}")

        #self.print_msg(list)

    def check_available_krw(self, list, isForce=False):
        #보유하고 있는 현금을 기준으로 비율을 정산합니다.

        #krw_total = get_balance("KRW")

        #이미 보유하고 있는 코인이면 구매한것으로 간주합니다.
        balances = self.upbit.get_balances()
        #print(f"check_available_krw : {balances}")

        for i in range(len(list)):
            if list[i]['is_buy'] == False:
                continue

            is_find = False
            for b in balances:
                if b['currency'] == list[i]['name'].replace('KRW-', ''):
                    is_find = True
                    break

            if is_find == False:
                #메모리상 is_buy true로 되어있데 ,balance에는 존재하지 않는 경우.?
                #이거는 외부에서 매도를 한것으로 간주해야합니다.
                #list[i]['is_sell'] = True 처리해야합니다.
                list[i]['is_sell'] = True


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

            # if self.is_test and list[i]['name'] == "KRW-BTC":
            #     list[i]['is_buy'] = True
            #     list[i]['is_sell'] = True
                
            #매수를 했지만 아직 매도를 하지 않은 코인은 비율 계산에서 제외합니다.    
            if list[i]['is_buy'] == True and list[i]['is_sell'] == False:
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

    def load_module(self, folder, module_name):
        file_path = os.path.join(folder, module_name + ".py")

        # 1. sys.modules에서 모듈이 이미 import되었는지 확인
        if module_name in sys.modules:
            if self.is_test:
                self.print_msg(f"'{module_name}' 모듈이 이미 sys.modules에 있습니다.")
            return sys.modules[module_name]

        # 2. 파일 경로에서 모듈 스펙 생성
        if not os.path.isfile(file_path):
            self.print_msg(f"'{file_path}' 파일이 존재하지 않습니다.")
            return None

        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None:
            self.print_msg(f"'{file_path}' 모듈 스펙을 생성할 수 없습니다.")
            return None

        # 3. 모듈 생성 및 로드
        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)

            # 4. sys.modules에 모듈 추가
            sys.modules[module_name] = module
            self.print_msg(f"'{module_name}' 모듈을 성공적으로 로드하고 sys.modules에 추가했습니다.")
            return module
        except Exception as e:
            self.print_msg(f"모듈 로드 중 오류 발생: {e}")
            return None
    
    def coin_main_loop(self, isForce):
        
        try:
            current_date = datetime.datetime.now().date()
            if self.last_checked_date is None or self.last_checked_date != current_date:
                self.simple_data.delete_common_data(10)
                self.last_checked_date = current_date
        except Exception as e:
            print(e)
            self.print_msg(f"[ERROR DELETE DB] {e}")
    
        try:
            if self.is_pause:
                return
            
            now = datetime.datetime.now()
            start_wait_time = now.replace(hour=7, minute=0, second=0, microsecond=0)
            end_wait_time = now.replace(hour=9, minute=0, second=0, microsecond=0)

            if start_wait_time <= now <= end_wait_time:
                self.is_waiting = True
            elif self.is_waiting == True:
                self.is_waiting = False
                self.make_coin_list(self.list_coin_info)
         
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
                        coin_info['krw_avaiable'] = -1
                        coin_info['check_buy_count'] = coin_info['check_buy_count_origin']
                        coin_info['best_k'] = find_best_k.GetBestK(coin_info['name'])
                        self.print_msg(f"[REPEAT] {coin_info['name']}.")
                        count_re_process += 1
                    # else:
                    #     #시간되면 무조건 매도 조건이 붙어있는경우.
                    #     list_check = coin_info['check_sell']
                    #     is_have_check_sell_time = False
                    #     if 0 < len(list_check):
                    #         for j in range(len(list_check)):
                    #             check_name = list_check[j]
                    #             if "check_sell_time" in check_name:
                    #                 is_have_check_sell_time = True
                    #                 break
                    #     else:
                    #         self.print_msg(f"[ERROR1] {coin_info['name']}. check_sell list 0")

                    #     if is_have_check_sell_time:
                    #         now = datetime.datetime.now()
                    #         end_time_wait = now.replace(hour=9, minute=0, second=0, microsecond=0)
                    #         if end_time_wait <= now:
                    #             coin_info['is_buy'] = False
                    #             coin_info['is_sell'] = False
                    #             coin_info['krw_avaiable'] = -1
                    #             coin_info['check_buy_count'] = coin_info['check_buy_count_origin']
                    #             coin_info['best_k'] = find_best_k.GetBestK(coin_info['name'])
                    #             self.print_msg(f"[INIT] {coin_info['name']}. best_k:{coin_info['best_k']}")
                    #             count_re_process += 1
                        
                else:
                    #매도 혹은 매수 프로세스를 해야합니다.
                    if coin_info['is_buy'] == True:
                        #매수를 했었다면 매도 체크 프로세스를 실행.

                        #체크 메서드를 루프로 실행해서 체크한다.
                        check_complete_count = 0
                        list_check = coin_info['check_sell']
                        if 0 < len(list_check):
                            for j in range(len(list_check)):
                                check_name = list_check[j]["module"]
                                condition = TypeCondition(list_check[j]["condition"])
                                checker_module = self.load_module("check", check_name)
                                if checker_module and hasattr(checker_module, check_name):
                                    method = getattr(checker_module, check_name)
                                    if method(coin_info, balances, self.config, self.print_msg, isForce, self.is_test) == True:
                                        check_complete_count+=1
                        else :
                            self.print_msg(f"[ERROR2] {coin_info['name']}. check_sell list 0")
                        
                        #매도 체크 조건은 하나만 만족한다면 매도처리!            
                        if(0 < check_complete_count):
                            module_name = "trade_sell"
                            module = self.load_module("trade", module_name)
                            if module and hasattr(module, module_name):
                                method = getattr(module, module_name)
                                method(self.upbit, coin_info, balances, self.config, self.simple_data, self.print_msg, isForce, self.is_test)
                                count_sell_process+=1
                    else:
                        #매수가 가능한지 체크 프로세스를 실행.

                        #체크 메서드를 루프로 실행해서 체크한다.
                        check_complete_count = 0
                        list_check = coin_info['check_buy']
                        if 0 < len(list_check):
                            for j in range(len(list_check)):
                                check_name = list_check[j]["module"]
                                condition = TypeCondition(list_check[j]["condition"])
                                checker_module = self.load_module("check", check_name)
                                if checker_module and hasattr(checker_module, check_name):
                                    method = getattr(checker_module, check_name)
                                    if method(coin_info, balances, self.config, self.print_msg, isForce, self.is_test) == True:
                                        check_complete_count+=1
                        else:
                            self.print_msg(f"[ERROR3] {coin_info['name']}. check_buy list 0")

                        #매수 체크 조건을 모두 만족했다!    
                        is_check_buy_count = coin_info['is_check_buy_count']
                        check_buy_count = coin_info['check_buy_count']
                        if(len(list_check) <= check_complete_count):
                            #매수 체크 조건을 모두 만족했다!

                            if is_check_buy_count:

                                #매수 카운팅을 체크합니다.
                                if check_buy_count <= 0:
                                    #매수합니다.
                                    module_name = "trade_buy"
                                    module = self.load_module("trade", module_name)
                                    if module and hasattr(module, module_name):
                                        method = getattr(module, module_name)
                                        method(self.upbit, coin_info, balances, self.config, self.simple_data, self.print_msg, isForce, self.is_test)
                                        count_buy_process+=1
                                else:
                                    #체크완료 카운트를 하나 뺍니다.
                                    set_check_count = check_buy_count - 1
                                    coin_info['check_buy_count'] = set_check_count
                                    self.print_msg(f"[CHECK BUY] {coin_info['name']}.  remain check count:{set_check_count}")

                            else:
                                module_name = "trade_buy"
                                module = self.load_module("trade", module_name)
                                if module and hasattr(module, module_name):
                                    method = getattr(module, module_name)
                                    method(self.upbit, coin_info, balances, self.config, self.simple_data, self.print_msg, isForce, self.is_test)

                        #매수 체크 조건을 불만족했다면 check_buy_count 초기화.
                        elif is_check_buy_count and check_buy_count != coin_info['check_buy_count_origin']:
                            coin_info['check_buy_count'] = coin_info['check_buy_count_origin']
                            self.print_msg(f"[CHECK RESET] {coin_info['name']}")

            #if 0 < count_re_process or 0 < count_sell_process or 0 < count_buy_process:
            self.check_available_krw(self.list_coin_info, isForce)
        except Exception as e:
            self.print_msg(f"[ERROR] {e}")
            # 예외가 발생한 위치와 스택 트레이스를 출력
            traceback_str = traceback.format_exc()
            self.print_msg(f"[TRACEBACK]\n{traceback_str}")

            
