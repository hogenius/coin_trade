from exchange_rate import ExchangeRater
import pyupbit

def get_current_price( ticker):
    """현재가 조회"""
    return pyupbit.get_orderbook(ticker=ticker)["orderbook_units"][0]["ask_price"]
       
#환율 기준으로 체크한다.
def check_buy_exchange_rate(coin_info, balances, config, simple_data, print_msg, isForce, isTest):
    coin_name = coin_info['name']
    rate_usd = ExchangeRater.Instance().GetUSD()
    current_price = get_current_price(coin_name)

    is_low_price_state = current_price < rate_usd
    print_msg(f"{coin_name} - check_exchange_rate: current:{current_price:,.2f} < e_rate_usd:{rate_usd:,.2f} = {is_low_price_state}", isForce)

    return is_low_price_state

    