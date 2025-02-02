import datetime

#무조건 판매 시간인지 체크한다.
def check_sell_time(coin_info, balances, config, simple_data, print_msg, isForce, isTest):
    now = datetime.datetime.now()
    end_time = now.replace(hour=7, minute=0, second=0, microsecond=0)
    start_time = end_time - datetime.timedelta(seconds=config.loop_sec*3)

    #매도 시간 KST 06:57 ~ 07:00
    return start_time < now < end_time

    