import asyncio
import pyupbit
from config import ConfigInfo
from statistics import stdev
from simple_data.simpledata import SimpleData
from simple_data.simpledata import TableType

class CheckTicker:
    
    def __init__(self, name, isTest):
        self.OUTLIER_COUNT = 3
        self.is_test = isTest
        self.config = ConfigInfo.Instance()
        self.list_ticker = []
        self.list_ticker_warning = []
        self.list_spike = []
        self.simple_data = SimpleData(ConfigInfo.Instance().db_path)

    async def InitRoutine(self):
        print("InitRoutine Start")

        self.MakeTickerList(self.list_ticker, self.list_ticker_warning)

        while True:
            await self.CheckList(self.list_ticker, "minutes3", 200)
            await asyncio.sleep(ConfigInfo.Instance().loop_sec)

    def print_msg(self, msg, withDiscord=True):
        if withDiscord:
            self.simple_data.add_string(TableType.Msg, msg)
            #Messaging.Instance().Send(msg)

    def MakeTickerList(self, listTicker, listTickerWarning):

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

    async def CheckTickerProcess(self, ticker, listTickerSpike, interval, checkCount):

        #print(f"CheckTicker:{ticker['market']}, interval:{interval}, checkCount:{checkCount}")
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
        list_volume_before = list_volume[0:len(list_volume) - self.OUTLIER_COUNT]
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
        

    async def CheckList(self, list_ticker, interval, checkCount):
        count = 0
        for ticker in list_ticker:
            await self.CheckTickerProcess(ticker, self.list_spike, interval, checkCount)
            count += 1
            await asyncio.sleep(0.1)

            if self.is_test and 5 <= count:
                break
        
        if(0 < len(self.list_spike) ):
            self.print_msg(f"spike coin find!! : {self.list_spike}")
            self.simple_data.add_string(TableType.Check, "BUY_COIN_LIST")
            #EventManager.Instance().Event("BUY_COIN_LIST", self.list_spike)
        else:
            if self.is_test:
                self.print_msg(f"no spike coin..")

                list_test = []
                list_test.append({
                'name':"hogenus3", 
                'stdev_volume_before':5,
                'stdev_volume':34
                })
                list_test.append({
                'name':"hogenus2", 
                'stdev_volume_before':62,
                'stdev_volume':6
                })
                list_test.append({
                'name':"hogenus1", 
                'stdev_volume_before':999,
                'stdev_volume':888
                })
                list_test.append({
                'name':"hogenus67", 
                'stdev_volume_before':136,
                'stdev_volume':99
                })

                EventManager.Instance().Event("BUY_COIN_LIST", list_test)

            