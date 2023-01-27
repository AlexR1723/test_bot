from quart import Quart
from logger import create_logger
from quart import request
from telegram.ext import Updater
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

import datetime,time
log = create_logger('app.log', 'app', 10)

token="5802197857:AAFu-F88ekbr3kvB745HE3Iqt7oEVm6fOAU"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")
# updater = Updater(token=token, use_context=True)
# import os
# from dotenv import load_dotenv, find_dotenv
# load_dotenv(find_dotenv())
# SECRET_KEY = os.environ.get("SECRET_KEY")
# DATABASE_PASSWORD = os.environ.get("DATABASE_PASSWORD")

# app = Quart(__name__)


# @app.route("/",methods=["POST"])
# async def webhook():
#     data = await request.get_json()
#     log.debug(f'good: {data}')
#     # with open('fuck','w') as f:
#     #     f.write(f'{datetime.datetime.now()}: {data}')
#     return {"input": data, "extra": True}


if __name__ == "__main__":
    application = ApplicationBuilder().token(token).build()

    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)

    application.run_polling()
    # log.debug(f'start app')
    # app.run(host="0.0.0.0",port=5000)
