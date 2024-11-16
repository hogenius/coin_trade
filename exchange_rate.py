from singletone import SingletonInstane
import yfinance as yf

class ExchangeRater(SingletonInstane):

    def GetUSD(self):

        try:
            df = yf.download(tickers="KRW=X", period="1d", interval="1m")
            #print("현재 원/달러 환율:", df)
            #rate = df["Close"][-1]
            rate = df["Close"].iloc[-1].item() 
        except Exception as e:
            rate = -1
        
        return rate
    
if __name__ == '__main__':
    exchangeRater = ExchangeRater()
    print(f"test : {exchangeRater.GetUSD()}")
        

    

    