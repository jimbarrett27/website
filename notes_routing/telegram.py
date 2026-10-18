"""The chat side of routing: file the note, say where, offer one-tap corrections.

The note is already safe in its inbox folder before any of this runs, so every
failure here just leaves it there. Button choices are kept in a small JSON file
under :func:`util.paths.data_path` -- Telegram's 64-byte ``callback_data`` can't
hold a path, and a file survives the bot restarting between note and tap.
"""

import asyncio
import json
import secrets
import threading
from pathlib import Path

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Message, Update
from telegram.ext import CallbackQueryHandler, ContextTypes

from gcp_util.secrets import get_telegram_user_id
from notes_routing import filing, log, router
from util.logging_util import setup_logger
from util.paths import data_path
from voice_notes.vault import vault_dir

logger = setup_logger(__name__)

PENDING_FILE = "notes_routing_pending.json"
MAX_PENDING = 100
CALLBACK_PREFIX = "route"
LABELS = {"file": "📁 {}", "new": "🆕 New: {}", "inbox": "↩️ Back to inbox", "leave": "Leave in inbox"}

_lock = threading.Lock()


def _load() -> dict:
    path = data_path(PENDING_FILE)
    return json.loads(path.read_text()) if path.exists() else {}


def _store(pending: dict) -> None:
    path = data_path(PENDING_FILE)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(list(pending.items())[-MAX_PENDING:])))


def remember(note_path: Path, source: str, title: str | None, options: list[tuple[str, str]]) -> str:
    key = secrets.token_hex(4)
    with _lock:
        pending = _load()
        pending[key] = {"note": note_path.relative_to(vault_dir()).as_posix(), "source": source,
                        "title": title, "options": options}
        _store(pending)
    return key


def _take(key: str) -> dict | None:
    with _lock:
        pending = _load()
        entry = pending.pop(key, None)
        _store(pending)
    return entry


def keyboard(key: str, options: list[tuple[str, str]]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(LABELS[action].format(folder), callback_data=f"{CALLBACK_PREFIX}:{key}:{i}")]
        for i, (action, folder) in enumerate(options)
    ])


def settle(note_path: Path, *, transcript: str, hint: str | None,
           source: str) -> tuple[str, Path, str | None, list[tuple[str, str]]]:
    """Route and, when confident, file the note. Returns (reply, where it is now, title, button options)."""
    inbox = note_path.parent.relative_to(vault_dir()).as_posix()
    saved = f"📝 Saved to {inbox}/{note_path.name}"
    log.record(note_path, source, "inbox")

    try:
        route = router.route(transcript, hint, source)
    except Exception:
        logger.exception(f"Routing {note_path.name} failed; leaving it in {inbox}")
        return saved, note_path, None, []

    if route.confident:
        filed = filing.file_note(note_path, route.folder, route.title)
        log.record(filed, source, f"auto, {route.confidence:.2f}")
        options = [("file", c) for c in route.candidates] + [("inbox", inbox)]
        return f"📝 Filed to {route.folder}/{filed.name}", filed, route.title, options

    options = [("file", c) for c in route.candidates]
    if route.new_folder:
        options.append(("new", route.new_folder))
    if not options:
        return saved, note_path, route.title, []
    reply = f"{saved}\nNot sure where it belongs" + (f" — {route.reason}" if route.reason else ".")
    return reply, note_path, route.title, options + [("leave", inbox)]


async def route_and_reply(message: Message, note_path: Path, *, transcript: str,
                          hint: str | None, source: str) -> None:
    """The last step of handling a note: file it if we can, and tell the chat where it went."""
    try:
        reply, where, title, options = await asyncio.to_thread(
            settle, note_path, transcript=transcript, hint=hint, source=source)
    except Exception:
        logger.exception(f"Filing {note_path.name} failed")
        inbox = note_path.parent.relative_to(vault_dir()).as_posix()
        reply, options = f"📝 Saved to {inbox}/{note_path.name}", []

    if not options:
        await message.reply_text(reply)
        return
    key = await asyncio.to_thread(remember, where, source, title, options)
    await message.reply_text(reply, reply_markup=keyboard(key, options))


def apply_choice(key: str, index: int) -> str:
    entry = _take(key)
    if entry is None:
        return f"That choice has expired — {log.LOG_NOTE} says where the note is."
    note = vault_dir() / entry["note"]
    if not note.exists():
        return f"{entry['note']} has moved since — {log.LOG_NOTE} says where it is."

    action, folder = entry["options"][index]
    if action == "leave":
        return f"📝 Left in {folder}/{note.name}"
    if action == "inbox":
        moved = filing.file_note(note, folder, index=False)
        log.record(moved, entry["source"], "back to inbox")
        return f"↩️ Back in {folder}/{moved.name}"
    moved = filing.file_note(note, folder, entry["title"])
    log.record(moved, entry["source"], "new folder" if action == "new" else "chosen")
    return f"📝 Filed to {folder}/{moved.name}"


async def handle_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if update.effective_user.id != get_telegram_user_id():
        await query.answer("Unauthorised.")
        return
    await query.answer()

    _, key, index = query.data.split(":")
    try:
        text = await asyncio.to_thread(apply_choice, key, int(index))
    except Exception as e:
        logger.exception("Applying a routing choice failed")
        text = f"⚠️ Couldn't move it: {e}"[:500]
    await query.edit_message_text(text)


def get_handlers():
    return [CallbackQueryHandler(handle_choice, pattern=rf"^{CALLBACK_PREFIX}:")]
