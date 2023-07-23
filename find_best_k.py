import pyupbit
import numpy as np


def GetBestK():
    best_k = 0.1
    result = 0.0
    df = pyupbit.get_ohlcv("KRW-BTC",count=7)
    try:
        for k in np.arange(0.3, 0.8, 0.1):
            ror = get_ror_by_df(df, k)
            if result < ror:
                best_k = k
                result = ror
            print("%.1f %f" % (k, ror))
    except Exception as e:
        print(e)
    return best_k

def get_ror_by_df(df, k=0.5):
    #df = pyupbit.get_ohlcv("KRW-BTC",count=7)
    df['range'] = (df['high'] - df['low']) * k
    df['target'] = df['open'] + df['range'].shift(1)

    fee = 0.0
    df['ror'] = np.where(df['high'] > df['target'],
                         df['close'] / df['target'] - fee,
                         1)

    ror = df['ror'].cumprod()[-2]
    #print("%.1f %f" % (k, ror))
    return ror

print(f"GetBestK {GetBestK()}")