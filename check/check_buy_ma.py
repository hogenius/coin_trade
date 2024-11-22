import pyupbit
import pandas
       
#이동평균선을 구한다.
def check_buy_ma(coin_info, balances, config, print_msg, isForce, isTest):
    
    coin_name = coin_info['name']
    
    df = pyupbit.get_ohlcv(coin_name, count=config.ma_3)
    if df is None :
        print_msg(f"check_buy_ma get_ohlcv 일시적 error: {coin_name} / df == None")
        return False
    
    df['MA_1'] = df['close'].rolling(config.ma_1).mean()
    df['MA_2'] = df['close'].rolling(config.ma_2).mean()
    #df['MA_3'] = df['close'].rolling(config.ma_3).mean()
    pandas.set_option('display.float_format', lambda x: '%.1f' % x)

    last_data = df.iloc[(len(df)-1)]
    data_ma_1 = last_data['MA_1']
    data_ma_2 = last_data['MA_2']
    #data_ma_3 = last_data['MA_3']

    #print(f"{config.ma_1}ma:{data_ma_1}, {config.ma_2}ma:{data_ma_2}, {config.ma_3}ma:{data_ma_3}")
    #is_regulat_arr = (data_ma_3 < data_ma_2 < data_ma_1)

    #1번 이동평균이 2번 이동평균선보다 이상이면 정배열로 간주한다.
    is_regulat_arr = (data_ma_2 < data_ma_1)
    print_msg(f"{coin_name} - check_ma: {config.ma_2}ma:{data_ma_2} < {config.ma_1}ma:{data_ma_1} = {is_regulat_arr}", isForce)

    return is_regulat_arr

    