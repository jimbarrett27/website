"""Type a message to the voice notes bot and it becomes a note in Obsidian.

No transcription step, so the reply is just where it was filed.
"""

import asyncio

from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

from gcp_util.secrets import get_telegram_user_id
from notes_routing import telegram as routing
from text_notes import vault
from util.logging_util import setup_logger
from util.timezone import STOCKHOLM

logger = setup_logger(__name__)


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    if update.effective_user.id != get_telegram_user_id():
        await message.reply_text("Unauthorised.")
        return

    try:
        note_path = await asyncio.to_thread(
            vault.save_note, when=message.date.astimezone(STOCKHOLM), text=message.text)
    except Exception as e:
        logger.exception("Saving text note to the vault failed")
        await message.reply_text(f"⚠️ Couldn't save to Obsidian: {e}"[:500])
        return

    # Any "file this under…" is part of the message, so there's no separate hint.
    await routing.route_and_reply(message, note_path, transcript=message.text,
                                  hint=None, source="text")


def get_handlers():
    return [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text)]
