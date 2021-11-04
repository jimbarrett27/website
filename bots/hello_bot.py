"""
A simple hello world bot to learn about bot deployment
"""

from telegram.ext import CommandHandler, Updater

from bots.secrets import get_telegram_key


def launch_hello_bot():
    """
    Launches a very simple telegram bot
    """

    token = get_telegram_key()

    updater = Updater(token=token)

    dispatcher = updater.dispatcher

    def jim(update, context):
        text = f"jim, {' '.join(context.args)}"
        context.bot.send_message(chat_id=update.effective_chat.id, text=text)

    caps_handler = CommandHandler("jim", jim)
    dispatcher.add_handler(caps_handler)

    updater.start_polling()
