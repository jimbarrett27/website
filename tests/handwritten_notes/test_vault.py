"""Tests for handwritten_notes.vault -- where notes land and what they look like."""

from datetime import datetime

import pytest

from handwritten_notes import vault
from util.timezone import STOCKHOLM

WHEN = datetime(2026, 10, 9, 14, 32, 7, tzinfo=STOCKHOLM)
PAGES = [(b"page-one", "jpg"), (b"page-two", "png")]


@pytest.fixture(autouse=True)
def tmp_vault(tmp_path, monkeypatch):
    monkeypatch.setenv("OBSIDIAN_VAULT_DIR", str(tmp_path))
    return tmp_path


def _save(transcript="- [ ] Buy coffee", caption=None, pages=PAGES):
    return vault.save_note(when=WHEN, pages=pages, model="some/vision-model",
                           caption=caption, transcript=transcript)


def test_writes_note_and_page_images(tmp_vault):
    saved = _save()
    folder = tmp_vault / "Handwritten Notes"
    assert saved.note_path == folder / "2026-10-09 1432.md"
    assert saved.image_paths == [folder / "images" / "2026-10-09 1432 p1.jpg",
                                 folder / "images" / "2026-10-09 1432 p2.png"]
    assert [p.read_bytes() for p in saved.image_paths] == [b"page-one", b"page-two"]


def test_note_has_frontmatter_transcript_then_page_embeds():
    text = _save().note_path.read_text()
    assert text.startswith("---\ncreated: 2026-10-09T14:32:07+02:00\npages: 2\n")
    assert "model: some/vision-model\n" in text
    assert "  - handwritten-note\n" in text
    assert "---\n\n- [ ] Buy coffee\n\n## Pages\n\n" in text
    assert text.endswith("![[2026-10-09 1432 p1.jpg]]\n![[2026-10-09 1432 p2.png]]\n")


def test_caption_becomes_the_heading():
    text = _save(caption="Standup").note_path.read_text()
    assert "---\n\n# Standup\n\n- [ ] Buy coffee\n" in text


def test_same_minute_does_not_overwrite():
    _save("one")
    second = _save("two")
    assert second.note_path.name == "2026-10-09 1432 (2).md"
    assert "![[2026-10-09 1432 (2) p1.jpg]]" in second.note_path.read_text()


def test_does_not_collide_with_voice_notes(tmp_vault):
    (tmp_vault / "Voice Notes").mkdir()
    (tmp_vault / "Voice Notes" / "2026-10-09 1432.md").write_text("voice")
    assert _save().note_path.name == "2026-10-09 1432.md"


def test_figures_are_saved_beside_the_pages_and_embedded_in_place(tmp_vault):
    transcript = "before\n![[{{figure-1}}]]\nmiddle\n![[{{figure-2}}]]\nafter"
    saved = vault.save_note(when=WHEN, pages=PAGES, model="m", caption=None,
                            transcript=transcript, figures=[b"<svg>1</svg>", b"<svg>2</svg>"])
    images = tmp_vault / "Handwritten Notes" / "images"
    assert saved.figure_paths == [images / "2026-10-09 1432 fig1.svg",
                                  images / "2026-10-09 1432 fig2.svg"]
    assert [p.read_bytes() for p in saved.figure_paths] == [b"<svg>1</svg>", b"<svg>2</svg>"]
    assert ("before\n![[2026-10-09 1432 fig1.svg]]\nmiddle\n![[2026-10-09 1432 fig2.svg]]\nafter"
            in saved.note_path.read_text())


def test_no_figures_writes_no_svgs(tmp_vault):
    assert _save().figure_paths == []
    assert not list((tmp_vault / "Handwritten Notes" / "images").glob("*.svg"))
