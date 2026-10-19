"""Moving a note from the inbox to where it belongs.

Only the ``.md`` moves. Its audio and page images stay in the inbox's attachment
folders: their names are unique and Obsidian resolves ``![[name]]`` anywhere in
the vault, so the embeds keep working wherever the note goes.

Each topic folder keeps an ``_index.md`` with a dated link per note, which makes
a study folder read as a log of the journey. A note leaving a folder takes its
line with it.
"""

import os
import re
from datetime import date
from pathlib import Path

from notes_routing.vault_map import INDEX_NOTE
from util.logging_util import setup_logger
from voice_notes.vault import vault_dir, write_atomic

logger = setup_logger(__name__)

CREATED = re.compile(r"^created: (\d{4}-\d{2}-\d{2})", re.MULTILINE)


def link(note_path: Path) -> str:
    """A wikilink by vault path, so two notes with the same title in different folders don't collide."""
    target = note_path.relative_to(vault_dir()).with_suffix("").as_posix()
    return f"[[{target}|{note_path.stem}]]"


def free_name(folder: Path, title: str) -> Path:
    path, n = folder / f"{title}.md", 1
    while path.exists():
        n += 1
        path = folder / f"{title} ({n}).md"
    return path


def _created(text: str) -> str:
    match = CREATED.search(text)
    return match.group(1) if match else date.today().isoformat()


def _drop_from_index(note_path: Path) -> None:
    index = note_path.parent / INDEX_NOTE
    if not index.exists():
        return
    lines = index.read_text(encoding="utf-8").splitlines(keepends=True)
    kept = [line for line in lines if link(note_path) not in line]
    if len(kept) != len(lines):
        write_atomic(index, "".join(kept).encode("utf-8"))


def _add_to_index(note_path: Path, created: str) -> None:
    index = note_path.parent / INDEX_NOTE
    existing = index.read_text(encoding="utf-8") if index.exists() else ""
    if existing and not existing.endswith("\n"):
        existing += "\n"
    write_atomic(index, f"{existing}- {created} {link(note_path)}\n".encode("utf-8"))


def file_note(note_path: Path, folder: str, title: str | None = None, *, index: bool = True) -> Path:
    """Move ``note_path`` into vault folder ``folder``, renamed to ``title`` if given. Returns the new path."""
    target_dir = vault_dir() / folder
    target_dir.mkdir(parents=True, exist_ok=True)
    target = free_name(target_dir, title or note_path.stem)
    created = _created(note_path.read_text(encoding="utf-8"))

    # The move is what matters; a stale or missing index line is only cosmetic.
    try:
        _drop_from_index(note_path)
    except Exception:
        logger.exception(f"Removing {note_path.name} from its folder's index failed")
    os.replace(note_path, target)
    if index:
        try:
            _add_to_index(target, created)
        except Exception:
            logger.exception(f"Adding {target.name} to its folder's index failed")

    logger.info(f"Filed {note_path.name} → {target.relative_to(vault_dir())}")
    return target
