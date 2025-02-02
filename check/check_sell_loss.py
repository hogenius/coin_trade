import pyupbit

def get_revenue_rate( balances, ticker):
    revenue_rate = 0.0

    for coin in balances:
        # 티커 형태로 전환
        coin_ticker = coin['unit_currency'] + "-" + coin['currency']

        if ticker == coin_ticker:
            # 현재 시세
            now_price = pyupbit.get_current_price(coin_ticker)
            
            # 수익률 계산을 위한 형 변환
            revenue_rate = (now_price - float(coin['avg_buy_price'])) / float(coin['avg_buy_price']) * 100.0

    return revenue_rate
       
#손해비율 조건 상태인지 체크한다.
def check_sell_loss(coin_info, balances, config, simple_data, print_msg, isForce, isTest):
    coin_name = coin_info['name']
    rate_stop_loss = coin_info['rate_stop_loss']
    result = False
    if rate_stop_loss < 0:
        #매수한 상태이니 이제 수익률을 계산합니다.
        revenue_rate = get_revenue_rate(balances, coin_name)
        result = revenue_rate <= rate_stop_loss
        print_msg(f"{coin_name} - check sell: revenue_rate({revenue_rate}) <= rate_stop_loss({rate_stop_loss}) = {result}", isForce)
    return result

    