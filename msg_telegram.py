import telegram
from telegram.ext import (
    Application,
    CommandHandler
)
import asyncio
import datetime
from queue import Queue
from config import ConfigInfo
from singletone import SingletonInstane
from event import EventManager

class Messaging(SingletonInstane):

    def __init__(self):
        self.queue_msg = Queue()
        self.bot = telegram.Bot(ConfigInfo.Instance().telegram_token)

    def SetTest(self, isTest):
        self.is_test = isTest

    def Send(self, msg):
        now = datetime.datetime.now()
        if self.is_test:
            message = f"TestMode\n[{now.strftime('%Y-%m-%d %H:%M:%S')}]\n{str(msg)}"
        else:
            message = f"[{now.strftime('%Y-%m-%d %H:%M:%S')}]\n{str(msg)}"
        print(message)
        self.queue_msg.put(message)

    async def RoutineMsg(self):
        while True:
            if 0 < self.queue_msg.qsize():
                msg = self.queue_msg.get()
                await self.bot.send_message(chat_id=ConfigInfo.Instance().telegram_chat_id, text=msg)
            await asyncio.sleep(0)

    def InitHandler(self):
        print(f"InitHandler!!!")
        self.app = Application.builder().token(ConfigInfo.Instance().telegram_token).build()
        self.app.add_handler(CommandHandler("help", self.handler_help))
        self.app.add_handler(CommandHandler("refresh", self.handler_refresh))
        self.app.add_handler(CommandHandler("check", self.handler_check))
        self.app.add_handler(CommandHandler("reload_config", self.handler_reload_config))
        self.app.add_handler(CommandHandler("safemode", self.handler_safe_mode))
        self.app.add_handler(CommandHandler("normalmode", self.handler_normal_mode))
        self.app.add_handler(CommandHandler("pause", self.handler_pause))
        self.app.add_handler(CommandHandler("resume", self.handler_resume))
        
        self.app.run_polling()

    async def handler_help(self, update, context):
        await asyncio.sleep(0);
        print(f"handler_help!!!")
        self.Send("good day! what kind do you want?")

    async def handler_refresh(self, update, context):
        await asyncio.sleep(0);
        print(f"handler_refresh!!!")
        self.Send("refresh coin list start")
        EventManager.Instance().Event("REFRESH_COIN_LIST", "")

    async def handler_check(self, update, context):
        await asyncio.sleep(0);
        print(f"handler_check!!!")
        self.Send("check coin list start")
        EventManager.Instance().Event("CHECK_COIN_LIST", "")

    async def handler_reload_config(self, update, context):
        await asyncio.sleep(0);
        print(f"handler_reload_config!!!")
        self.Send("reload config start")
        EventManager.Instance().Event("RELOAD_CONFIG", "")

    async def handler_safe_mode(self, update, context):
        await asyncio.sleep(0);
        print(f"handler_safe_mode!!!")
        self.Send("safe mode start")
        EventManager.Instance().Event("SAFE_MODE", "")

    async def handler_normal_mode(self, update, context):
        await asyncio.sleep(0);
        print(f"handler_normal_mode!!!")
        self.Send("normal mode start")
        EventManager.Instance().Event("NORMAL_MODE", "")

    async def handler_pause(self, update, context):
        await asyncio.sleep(0);
        print(f"handler_pause!!!")
        self.Send("pause mode start")
        EventManager.Instance().Event("PAUSE", "")

    async def handler_resume(self, update, context):
        await asyncio.sleep(0);
        print(f"handler_resume!!!")
        self.Send("resume mode start")
        EventManager.Instance().Event("RESUME", "")    

'''
async def help_handler(update, context):
    print(f"help_handler!!!")
    await asyncio.sleep(0);

if __name__ == '__main__':
    print(f"__main__!!!")
    app = Application.builder().token(ConfigInfo.Instance().telegram_token).build()
    app.add_handler(CommandHandler("help", help_handler))
    app.run_polling()
'''

    