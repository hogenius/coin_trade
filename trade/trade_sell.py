import pyupbit

def get_balance(balances, ticker):
    """잔고 조회"""
    for b in balances:
        if b['currency'] == ticker:
            if b['balance'] is not None:
                return float(b['balance'])
            else:
                return 0
    return 0

def get_current_price(ticker):
    """현재가 조회"""
    return pyupbit.get_orderbook(ticker=ticker)["orderbook_units"][0]["ask_price"]

def trade_sell(upbit, coin_info, balances, config, print_msg, isForce, isTest):
        
    result = False
    coin_name_pure = coin_info['name'].replace('KRW-', '')
    coin_balance = get_balance(balances, coin_name_pure)
    if coin_balance > 0.00008:
        sell_coin = coin_balance*0.9995
        if isTest == False:
            upbit.sell_market_order(coin_info['name'], sell_coin)
        result = True
        sell_krw = get_current_price(coin_info['name']) * sell_coin
        if "buy_price" in coin_info:
            margin_krw = sell_krw - coin_info['buy_price']
            del coin_info['buy_price']
            print_msg(f"[SELL] {coin_info['name']}:{sell_coin}\nsell_krw:{sell_krw:,.2f}\nmargin_krw:{margin_krw:,.2f}")
        else:
            print_msg(f"[SELL] {coin_info['name']}:{sell_coin}\nsell_krw:{sell_krw:,.2f}\nmargin_krw:unknown")
        coin_info['is_sell'] = True
        coin_info['sell_price'] = sell_krw
    
    return result