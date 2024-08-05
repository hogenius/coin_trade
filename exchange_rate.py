from singletone import SingletonInstane
import yfinance as yf

class ExchangeRater(SingletonInstane):

    def GetUSD(self):
        df = yf.download("KRW=X")
        #print("현재 원/달러 환율:", df)
        rate = df["Close"][-1]

        return rate

#ExchangeRater.Test()
        

    

    