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

    