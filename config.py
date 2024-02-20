import yaml

class ConfigInfo:
    def __init__(self) -> None:
        with open('config.yaml') as f:
            config_data = yaml.load(f, Loader=yaml.FullLoader)
            self.access = config_data['key_access']
            self.secret = config_data['key_secret']
            self.coin_name = config_data['coin_name']
            self.ma_1 = config_data['ma_line_1']
            self.ma_2 = config_data['ma_line_2']
            self.ma_3 = config_data['ma_line_3']
            self.ma_check_sec = config_data['ma_check_sec']
            self.loop_sec = config_data['loop_sec']
            self.loop_check_sec = config_data['loop_check_sec']
            self.discord_hook = config_data['discord_hook']
            self.telegram_token = config_data['telegram_token']
            self.telegram_chat_id = config_data['telegram_chat_id']
            self.list_coin = config_data['list_coin']
