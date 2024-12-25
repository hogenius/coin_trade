import datetime
from simple_common.simpledata import SimpleData

def get_balance(balances, ticker):
    """잔고 조회"""
    for b in balances:
        if b['currency'] == ticker:
            if b['balance'] is not None:
                return float(b['balance'])
            else:
                return 0
    return 0

def trade_buy(upbit, coin_info, balances, config, simple_data:SimpleData, print_msg, isForce, isTest):
        
    krw_total = get_balance(balances, "KRW")
    krw = coin_info['krw_avaiable']

    #보완처리. 비율료 계산되었던 현금가용액이 실제 보유현금액보다 크다?
    if krw_total < krw:
        krw = krw_total

    if krw > 5000:
        buy_krw = krw*0.9995
        if isTest == False:
            upbit.buy_market_order(coin_info['name'], buy_krw)

        print_msg(f"[BUY] {coin_info['name']}:{buy_krw:,.2f}")

        #매수한것으로 표기. 하루에 반복적으로 구매 하지 않습니다.
        #하루가 지나서 전량 매도가 되기전에 사용자 임의로 매도를 할수 있도록 말이죠.

        try:
            simple_data.insert_common_data(
            "buy", 
            coin_info['name'], None, None, None, 
            buy_krw, None, None, None, 
            datetime.datetime.now(datetime.timezone.utc))
        except Exception as e:
            print(e)
            print_msg(f"[ERROR BUY DB] {e}")

        coin_info['is_buy'] = True
        coin_info['buy_price'] = buy_krw

        #print(f"after buy list_coin_info : {list_coin_info}")
    else:
        
        print_msg(f"[BUY ERROR] not enough money to buy_market_order {coin_info['name']}. krw:{krw:,.2f}")