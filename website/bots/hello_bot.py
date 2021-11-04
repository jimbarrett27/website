from telegram.ext import Updater
from telegram.ext import CommandHandler

from bots.secrets import get_telegram_key

def launch_hello_bot():

    token = get_telegram_key()

    updater = Updater(token=token)

    dispatcher = updater.dispatcher

    def jim(update, context):
        text = f"jim, {' '.join(context.args)}"
        context.bot.send_message(chat_id=update.effective_chat.id, text=text)

    caps_handler = CommandHandler('jim', jim)
    dispatcher.add_handler(caps_handler)

    updater.start_polling()
