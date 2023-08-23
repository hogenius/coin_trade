import requests
import datetime
from config import ConfigInfo
config = ConfigInfo()

def send(msg):
    now = datetime.datetime.now()
    message = {"content": f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] {str(msg)}"}
    requests.post(config.discord_hook, data=message)
    print(message)
