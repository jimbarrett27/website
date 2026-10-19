"""``Notes Log.md``: every note the bot saves or moves, oldest first.

The safety net for misfiling. Each move adds a fresh line rather than editing an
old one, so the last line mentioning a note says where it is now.
"""

from pathlib import Path

from notes_routing.filing import link
from util.logging_util import setup_logger
from util.timezone import stockholm_now
from voice_notes.vault import vault_dir, write_atomic

logger = setup_logger(__name__)

LOG_NOTE = "Notes Log.md"
HEADER = "# Notes log\n\nEvery note the bot saved or moved, oldest first.\n\n"


def record(note_path: Path, source: str, how: str) -> None:
    """Append one line; never raises, since losing a log line mustn't lose a note."""
    try:
        folder = note_path.parent.relative_to(vault_dir()).as_posix()
        line = f"- {stockholm_now():%Y-%m-%d %H:%M} · {source} · {link(note_path)} → {folder}/ ({how})\n"
        path = vault_dir() / LOG_NOTE
        existing = path.read_text(encoding="utf-8") if path.exists() else HEADER
        write_atomic(path, (existing + line).encode("utf-8"))
    except Exception:
        logger.exception(f"Writing {LOG_NOTE} failed for {note_path}")
