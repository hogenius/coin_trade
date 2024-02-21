import telegram
from telegram.ext import (
    Application,
    CommandHandler
)
import asyncio
import datetime
from config import ConfigInfo
config = ConfigInfo.Instance()
bot = telegram.Bot(config.telegram_token)

def send(msg):
    now = datetime.datetime.now()
    message = f"[{now.strftime('%Y-%m-%d %H:%M:%S')}]\n{str(msg)}"
    asyncio.run(bot.send_message(chat_id=config.telegram_chat_id, text=message))
    print(message)

async def help_handler(update, context):
    await bot.send_message(chat_id=config.telegram_chat_id, text=str(context))

if __name__ == '__main__':
    app = Application.builder().token(config.telegram_token).build()
    app.add_handler(CommandHandler("help", help_handler))
    app.run_polling()

