"""Filing typed messages into the Obsidian vault.

Same vault, same write rules as :mod:`voice_notes.vault`. ``Text Notes/`` is the
inbox; :mod:`notes_routing` moves the note on from there.
"""

from datetime import datetime
from pathlib import Path

from util.logging_util import setup_logger
from voice_notes.vault import free_stem, vault_dir, write_atomic

logger = setup_logger(__name__)

NOTES_FOLDER = "Text Notes"


def notes_dir() -> Path:
    return vault_dir() / NOTES_FOLDER


def render_note(*, when: datetime, text: str) -> str:
    return (
        "---\n"
        f"created: {when.isoformat(timespec='seconds')}\n"
        "source: telegram\n"
        "tags:\n"
        "  - text-note\n"
        "---\n"
        "\n"
        f"{text}\n"
    )


def save_note(*, when: datetime, text: str) -> Path:
    note_path = notes_dir() / f"{free_stem(notes_dir(), when)}.md"
    write_atomic(note_path, render_note(when=when, text=text).encode("utf-8"))
    logger.info(f"Saved text note {note_path.name} ({len(text)} chars)")
    return note_path
