import pyupbit
       
def get_target_price(ticker, k):
    """변동성 돌파 전략으로 매수 목표가 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=2)
    target_price = df.iloc[0]['close'] + (df.iloc[0]['high'] - df.iloc[0]['low']) * k
    return target_price

def get_current_price(ticker):
    """현재가 조회"""
    return pyupbit.get_orderbook(ticker=ticker)["orderbook_units"][0]["ask_price"]

def check_buy_vb(coin_info, balances, config, print_msg, isForce, isTest):
    coin_name = coin_info['name']
    bestK = coin_info['best_k']
    target_price = get_target_price(coin_name, bestK)
    current_price = get_current_price(coin_name)

    is_over_target_price = target_price < current_price
    print_msg(f"{coin_name} - check_vb: target:{target_price:,.2f} < current:{current_price:,.2f} = {is_over_target_price}", isForce)

    return is_over_target_price

    