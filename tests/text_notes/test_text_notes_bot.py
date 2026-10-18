"""Tests for typed notes: saved to the Text Notes inbox, then handed to the router."""

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from notes_routing import telegram as routing
from text_notes import text_notes_bot as bot

ME = 42
FOLDER = "Text Notes"


class FakeMessage:
    def __init__(self, text="Remember the milk."):
        self.text = text
        self.date = datetime(2026, 10, 9, 12, 32, tzinfo=timezone.utc)
        self.replies = []

    async def reply_text(self, text, **kwargs):
        self.replies.append(text)


def _update(message, user_id=ME):
    return SimpleNamespace(message=message, effective_user=SimpleNamespace(id=user_id))


@pytest.fixture(autouse=True)
def fakes(monkeypatch, tmp_path):
    monkeypatch.setenv("OBSIDIAN_VAULT_DIR", str(tmp_path))
    monkeypatch.setenv("JIMBARRETT_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setattr(bot, "get_telegram_user_id", lambda: ME)
    seen = []

    def fake_route(transcript, hint, source):
        seen.append((transcript, hint, source))
        return routing.router.Route(title=None)
    monkeypatch.setattr(routing.router, "route", fake_route)
    return SimpleNamespace(vault=tmp_path / FOLDER, seen=seen)


@pytest.mark.asyncio
async def test_message_is_saved_and_routed(fakes):
    message = FakeMessage()
    await bot.handle_text(_update(message), None)

    assert message.replies == [f"📝 Saved to {FOLDER}/2026-10-09 1432.md"]
    note = (fakes.vault / "2026-10-09 1432.md").read_text()
    assert note.startswith("---\ncreated: 2026-10-09T14:32:00+02:00\nsource: telegram\n")
    assert "  - text-note\n" in note and note.endswith("Remember the milk.\n")
    assert fakes.seen == [("Remember the milk.", None, "text")]


@pytest.mark.asyncio
async def test_rejects_other_users(fakes):
    message = FakeMessage()
    await bot.handle_text(_update(message, user_id=7), None)
    assert message.replies == ["Unauthorised."]
    assert not fakes.vault.exists() and fakes.seen == []


@pytest.mark.asyncio
async def test_vault_failure_is_reported_and_not_routed(monkeypatch, fakes):
    def broken(**kwargs):
        raise OSError("disk on fire")
    monkeypatch.setattr(bot.vault, "save_note", broken)

    message = FakeMessage()
    await bot.handle_text(_update(message), None)
    assert message.replies == ["⚠️ Couldn't save to Obsidian: disk on fire"]
    assert fakes.seen == []


def test_text_inbox_is_never_a_routing_target(tmp_path, monkeypatch):
    monkeypatch.setenv("OBSIDIAN_VAULT_DIR", str(tmp_path))
    (tmp_path / FOLDER).mkdir()
    (tmp_path / "Recipes").mkdir()
    assert [f.path for f in routing.router.vault_map.folders()] == ["Recipes"]
