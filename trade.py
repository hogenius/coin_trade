import asyncio
import pyupbit
from config import ConfigInfo
from test import test_class
from auto_trade_vb_ma_multi_class import CoinTrade
from msg_telegram import Messaging
from check_ticker import CheckTicker
is_test = False

if __name__ == '__main__':
    
    Messaging.Instance().SetTest(is_test)
    Messaging.Instance().Send("trade start")
    
    upbit = pyupbit.Upbit(ConfigInfo.Instance().access, ConfigInfo.Instance().secret)

    loop = asyncio.get_event_loop()
    loop.create_task(Messaging.Instance().RoutineMsg())
    #loop.create_task(test_class(upbit, is_test).InitRoutine())
    loop.create_task(CoinTrade("TRADER", upbit, is_test).InitRoutine())
    loop.create_task(CheckTicker("CHECKER", is_test).InitRoutine())
    
    Messaging.Instance().InitHandler()
    loop.run_forever()

    

    