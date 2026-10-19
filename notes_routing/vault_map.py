"""What the router knows about the vault: its folders, what they're for, what's in them.

Folders are the only filing targets -- the router never invents one. A folder can
describe itself in an ``_about.md``, written in Obsidian like any other note; that
is the main way to steer routing.
"""

from dataclasses import dataclass
from pathlib import Path

from handwritten_notes.vault import IMAGES_FOLDER, NOTES_FOLDER as HANDWRITTEN_FOLDER
from text_notes.vault import NOTES_FOLDER as TEXT_FOLDER
from voice_notes.vault import AUDIO_FOLDER, NOTES_FOLDER as VOICE_FOLDER, vault_dir

INBOX_FOLDERS = (VOICE_FOLDER, HANDWRITTEN_FOLDER, TEXT_FOLDER)
ABOUT_NOTE = "_about.md"
INDEX_NOTE = "_index.md"
# Attachment folders hold embeds, not notes.
SKIPPED_NAMES = {AUDIO_FOLDER, IMAGES_FOLDER, "attachments"}

RECENT_TITLES = 5
MAX_ABOUT_CHARS = 500
MAX_FOLDERS = 200


@dataclass(frozen=True)
class Folder:
    path: str  # relative to the vault, '/'-separated
    about: str
    recent: list[str]


def _skipped(rel: Path) -> bool:
    return (rel.parts[0] in INBOX_FOLDERS
            or any(part.startswith((".", "_")) or part in SKIPPED_NAMES for part in rel.parts))


def _recent_titles(folder: Path) -> list[str]:
    notes = [p for p in folder.glob("*.md") if not p.name.startswith("_")]
    notes.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return [p.stem for p in notes[:RECENT_TITLES]]


def folders() -> list[Folder]:
    root = vault_dir()
    if not root.is_dir():
        return []
    found = []
    for path in sorted(p for p in root.rglob("*") if p.is_dir()):
        rel = path.relative_to(root)
        if _skipped(rel):
            continue
        about = path / ABOUT_NOTE
        found.append(Folder(
            path=rel.as_posix(),
            about=about.read_text(encoding="utf-8").strip()[:MAX_ABOUT_CHARS] if about.exists() else "",
            recent=_recent_titles(path),
        ))
        if len(found) == MAX_FOLDERS:
            break
    return found
