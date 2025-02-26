from singletone import SingletonInstane
import yfinance as yf
import requests

class ExchangeRater(SingletonInstane):

    def GetUSD(self):

        return self.CheckWay2();
    
    def CheckWay(self):
        try:
            df = yf.download(tickers="KRW=X", period="1d", interval="1m")
            #print("현재 원/달러 환율:", df)
            #rate = df["Close"][-1]
            rate = df["Close"].iloc[-1].item() 
        except Exception as e:
            rate = -1
        
        return rate
    
    def CheckWay2(self):

        url = "https://api.exchangerate-api.com/v4/latest/USD"
        try:
            response = requests.get(url)
            data = response.json()
            rate = data["rates"]["KRW"]
            #rate : 1431.48
        except Exception as e:
            rate = -1
        
        return rate
    
if __name__ == '__main__':
    exchangeRater = ExchangeRater()
    print(f"test : {exchangeRater.GetUSD()}")
        

    

    