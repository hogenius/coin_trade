import asyncio
import pyupbit
from config import ConfigInfo
from test import test_class
from auto_trade_check import CoinTrade
from msg_telegram import Messaging
from check_ticker import CheckTicker

is_test = True

if __name__ == '__main__':
    
    #Messaging.Instance().SetTest(is_test);
    #Messaging.Instance().Send("trade start")
    ConfigInfo.Instance().LoadConfig('config_hmm.yaml')
    ConfigInfo.Instance().LoadSecurity('security.yaml')
    
    upbit = pyupbit.Upbit(ConfigInfo.Instance().access, ConfigInfo.Instance().secret)

    loop = asyncio.get_event_loop()
    #loop.create_task(Messaging.Instance().RoutineMsg())
    #loop.create_task(test_class(upbit, is_test).InitRoutine())
    coin_trade = CoinTrade("TRADER", upbit, is_test)
    loop.create_task(coin_trade.InitRoutine())
    loop.create_task(coin_trade.InitPollingRoutine())
    #loop.create_task(CheckTicker("CHECKER", is_test).InitRoutine())
    
    #Messaging.Instance().InitHandler()
    loop.run_forever()