import pyupbit
import yaml
import pandas

from backtesting import Backtest, Strategy
from backtesting.lib import crossover
from backtesting.test import SMA, GOOG

access = ""
secret = ""
coin_name = ""
ma_1 = 0
ma_2 = 0
ma_3 = 0
ma_check_sec = 0

class SmaCross(Strategy):
    def init(self):
        price = self.data.Close
        self.ma1 = self.I(SMA, price, ma_1)
        self.ma2 = self.I(SMA, price, ma_2)
        #self.ma3 = self.I(SMA, price, ma_3)

    def next(self):
        if crossover(self.ma1, self.ma2):
            print(f"buy")
            self.buy()
        elif crossover(self.ma2, self.ma1):
            print(f"sell")
            self.sell()

print("autotrade start")

with open('config.yaml') as f:
    config_data = yaml.load(f, Loader=yaml.FullLoader)
    access = config_data['key_access']
    secret = config_data['key_secret']
    coin_name = config_data['coin_name']
    ma_1 = config_data['ma_line_1']
    ma_2 = config_data['ma_line_2']
    ma_3 = config_data['ma_line_3']
    ma_check_sec = config_data['ma_check_sec']

upbit = pyupbit.Upbit(access, secret)

df = pyupbit.get_ohlcv(coin_name, count=200)
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

