import yaml
from singletone import SingletonInstane

class ConfigInfo(SingletonInstane):
    
    def LoadConfig(self, fileName):
        self.configFileName = fileName
        with open(fileName) as f:
            config_data = yaml.load(f, Loader=yaml.FullLoader)
            self.coin_name = config_data['coin_name']
            self.ma_1 = config_data['ma_line_1']
            self.ma_2 = config_data['ma_line_2']
            self.ma_3 = config_data['ma_line_3']
            self.ma_check_sec = config_data['ma_check_sec']
            self.loop_sec = config_data['loop_sec']
            self.loop_check_sec = config_data['loop_check_sec']
            self.list_coin = config_data['list_coin']
            self.db_path = config_data['db_path']
            self.polling_sec = config_data['polling_sec']
            

    def LoadSecurity(self, fileName):
        self.securityFileName = fileName
        with open(fileName) as s:
            security_data = yaml.load(s, Loader=yaml.FullLoader)
            self.access = security_data['key_access']
            self.secret = security_data['key_secret']
            self.discord_hook = security_data['discord_hook']
            self.telegram_token = security_data['telegram_token']
            self.telegram_chat_id = security_data['telegram_chat_id']

    def ReloadAll(self):
        self.LoadConfig(self.configFileName)
        self.LoadSecurity(self.securityFileName)
