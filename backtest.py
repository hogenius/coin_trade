import pyupbit
import pandas

from numbers import Number
from typing import Sequence
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
from backtesting.test import SMA, GOOG
from config import ConfigInfo
config = ConfigInfo()

class SmaCross(Strategy):
    is_buy = False

    def init(self):
        price = self.data.Close
        self.ma1 = self.I(SMA, price, config.ma_1)
        self.ma2 = self.I(SMA, price, config.ma_2)
        self.ma3 = self.I(SMA, price, config.ma_3)

    def next(self):
        try:
            series1 = (
                self.ma1.values if isinstance(self.ma1, pandas.Series) else
                (self.ma1, self.ma1) if isinstance(self.ma1, Number) else
                self.ma1)

            series2 = (
                self.ma2.values if isinstance(self.ma2, pandas.Series) else
                (self.ma2, self.ma2) if isinstance(self.ma2, Number) else
                self.ma2)

            series3 = (
                self.ma3.values if isinstance(self.ma3, pandas.Series) else
                (self.ma3, self.ma3) if isinstance(self.ma3, Number) else
                self.ma3)
        
        
            #if crossover(self.ma1, self.ma2):
            case1 = (series3[-2] < series2[-2] < series1[-2])
            case2 = (series3[-1] < series2[-1] < series1[-1])
            #print(f"next check {case1} / {case2}")
            if SmaCross.is_buy == False and case1 == False and case2 == True:
                print(f"buy")
                self.position.close()
                self.buy()
                SmaCross.is_buy = True
            elif SmaCross.is_buy == True and crossover(self.ma2, self.ma1):
                print(f"sell")
                self.position.close()
                self.sell()
                SmaCross.is_buy = False
        except IndexError:
            print("index error")
        
        

print("autotrade start")

upbit = pyupbit.Upbit(config.access, config.secret)

df = pyupbit.get_ohlcv(config.coin_name, count=200)
#df = df.drop(['value'], axis=1)
#df['datetime'].dt.strftime('%Y-%m-%d')
df = df.rename(columns={'open':'Open', 'high':'High', 'low':'Low', 'close':'Close', 'volume':'Volume'})

#print(df)
# print(GOOG)

bt = Backtest(df, SmaCross, cash=100000000.0, commission=.0005,
              exclusive_orders=True)
stats = bt.run()
bt.plot()

stats = stats.rename(index={'Start':'시작','End':'종료','Duration':'기간','Exposure Time [%]':'노출 시간 [%]','Equity Final [$]':'자본 최종 [$]','Equity Peak [$]':'자기자본 피크 [$]','Return [%]':'수익률 [%]','Buy & Hold Return [%]':'매수 후 보유 수익률','Return (Ann.) [%]':'수익률 (Ann.) [%]','Volatility (Ann.) [%]':'변동성 (Ann.) [%]','Sharpe Ratio':'샤프 비율','Sortino Ratio':'소르티노 비율','Calmar Ratio':'칼마 비율','Max. Drawdown [%]':'최대 하락폭  [%]','Avg. Drawdown [%]':'평균 하락폭  [%]','Max. Drawdown Duration':'최대 인출기간','Avg. Drawdown Duration':'평균 인출 기간','# Trades':'# 거래','Win Rate [%]':'승률 [%]','Best Trade [%]':'최고의 거래 [%]','Worst Trade [%]':'최악의 거래 [%]','Avg. Trade':'평균 거래','Max. Trade Duration':'최대 거래 기간','Avg. Trade Duration':'평균 거래 기간','Profit Factor':' 이익 요인','Expectancy [%]':'기대치 [%]'})

print(stats)

