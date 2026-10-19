"""Tests for notes_routing -- the vault map, the router's checks, filing, the log, and the buttons."""

import json
from types import SimpleNamespace

import pytest

from notes_routing import filing, log, router, telegram, vault_map

ME = 42
NOTE = "---\ncreated: 2026-10-09T14:32:07+02:00\nsource: telegram\n---\n\nAttention is a soft lookup.\n"


@pytest.fixture(autouse=True)
def vault(tmp_path, monkeypatch):
    root = tmp_path / "vault"
    monkeypatch.setenv("OBSIDIAN_VAULT_DIR", str(root))
    monkeypatch.setenv("JIMBARRETT_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setattr(telegram, "get_telegram_user_id", lambda: ME)
    (root / "Study" / "Transformers").mkdir(parents=True)
    (root / "Study" / "Transformers" / "_about.md").write_text("Notes from the transformers → LLMs journey.")
    (root / "Study" / "Transformers" / "Tokenisation.md").write_text("BPE")
    (root / "Recipes").mkdir()
    (root / "Voice Notes" / "audio").mkdir(parents=True)
    (root / ".obsidian").mkdir()
    return root


def _inbox_note(vault, name="2026-10-09 1432.md"):
    path = vault / "Voice Notes" / name
    path.write_text(NOTE)
    return path


def _reply(**fields):
    return json.dumps({"folder": None, "confidence": 0, "candidates": [], "new_folder": None,
                       "title": "Attention as soft lookup", "reason": "", **fields})


KNOWN = {"Recipes", "Study", "Study/Transformers"}


# --- vault map -----------------------------------------------------------------

def test_vault_map_lists_topic_folders_with_descriptions_and_recent_notes():
    folders = {f.path: f for f in vault_map.folders()}
    assert set(folders) == KNOWN  # no inbox, attachments or hidden folders
    assert folders["Study/Transformers"].about.startswith("Notes from the transformers")
    assert folders["Study/Transformers"].recent == ["Tokenisation"]  # _about.md isn't a note


# --- router --------------------------------------------------------------------

def test_parse_accepts_a_known_folder_inside_chatter():
    route = router.parse("Sure!\n```json\n" + _reply(folder="Study/Transformers", confidence=0.9,
                                                       candidates=["Study", "Nowhere"]) + "\n```", KNOWN)
    assert route.folder == "Study/Transformers" and route.confident
    assert route.candidates == ["Study"]
    assert route.title == "Attention as soft lookup"


def test_parse_never_files_into_a_folder_that_does_not_exist():
    route = router.parse(_reply(folder="Study/Made Up", confidence=0.99), KNOWN)
    assert route.folder is None and not route.confident


def test_parse_cleans_titles_and_rejects_escaping_new_folders():
    route = router.parse(_reply(title='What is "Q/K/V"?', new_folder="../etc"), KNOWN)
    assert route.title == "What is Q K V"
    assert route.new_folder is None
    assert router.parse(_reply(new_folder="Study/Diffusion"), KNOWN).new_folder == "Study/Diffusion"


def test_parse_rejects_garbage():
    with pytest.raises(ValueError):
        router.parse("I'd put it in Recipes.", KNOWN)


def test_route_passes_the_vault_and_hint_to_the_prompt(monkeypatch):
    seen = {}

    def fake_llm(template, params):
        seen.update(params)
        return _reply(folder="Recipes", confidence=0.8)
    monkeypatch.setattr(router, "get_llm_response", fake_llm)

    assert router.route("pancakes", "breakfast", "voice").folder == "Recipes"
    assert seen["hint"] == "breakfast"
    assert {f.path for f in seen["folders"]} == KNOWN


# --- filing and the log --------------------------------------------------------

def test_file_note_moves_renames_and_indexes(vault):
    note = _inbox_note(vault)
    filed = filing.file_note(note, "Study/Transformers", "Attention as soft lookup")

    assert filed == vault / "Study" / "Transformers" / "Attention as soft lookup.md"
    assert filed.read_text() == NOTE and not note.exists()
    assert (vault / "Study" / "Transformers" / "_index.md").read_text() == (
        "- 2026-10-09 [[Study/Transformers/Attention as soft lookup|Attention as soft lookup]]\n")


def test_file_note_dedupes_titles_and_leaves_the_old_index(vault):
    first = filing.file_note(_inbox_note(vault, "a.md"), "Recipes", "Pancakes")
    second = filing.file_note(_inbox_note(vault, "b.md"), "Recipes", "Pancakes")
    assert second.name == "Pancakes (2).md"

    filing.file_note(first, "Study", "Pancakes")
    index = (vault / "Recipes" / "_index.md").read_text()
    assert "Recipes/Pancakes|" not in index and "Recipes/Pancakes (2)|" in index


def test_log_appends_a_line_per_event(vault):
    note = _inbox_note(vault)
    log.record(note, "voice", "inbox")
    filed = filing.file_note(note, "Recipes", "Pancakes")
    log.record(filed, "voice", "chosen")

    lines = (vault / log.LOG_NOTE).read_text().splitlines()
    assert lines[0] == "# Notes log"
    assert lines[-2].endswith("· voice · [[Voice Notes/2026-10-09 1432|2026-10-09 1432]] → Voice Notes/ (inbox)")
    assert lines[-1].endswith("· voice · [[Recipes/Pancakes|Pancakes]] → Recipes/ (chosen)")


def test_log_failure_is_swallowed(vault, tmp_path):
    log.record(tmp_path / "outside the vault.md", "voice", "inbox")  # must not raise
    assert not (vault / log.LOG_NOTE).exists()


# --- the chat side -------------------------------------------------------------

class FakeMessage:
    def __init__(self):
        self.replies = []

    async def reply_text(self, text, reply_markup=None, **kwargs):
        self.replies.append((text, reply_markup))


def _buttons(markup):
    return [(b.text, b.callback_data) for row in markup.inline_keyboard for b in row]


def _route_to(monkeypatch, **fields):
    monkeypatch.setattr(router, "get_llm_response", lambda template, params: _reply(**fields))


async def _tap(callback_data, user_id=ME):
    edits = []

    async def edit(text, **kwargs):
        edits.append(text)

    async def answer(*args, **kwargs):
        pass
    query = SimpleNamespace(data=callback_data, answer=answer, edit_message_text=edit)
    await telegram.handle_choice(
        SimpleNamespace(callback_query=query, effective_user=SimpleNamespace(id=user_id)), None)
    return edits


@pytest.mark.asyncio
async def test_confident_route_files_and_offers_a_way_back(vault, monkeypatch):
    _route_to(monkeypatch, folder="Study/Transformers", confidence=0.9, candidates=["Study"])
    message = FakeMessage()
    await telegram.route_and_reply(message, _inbox_note(vault), transcript="…", hint=None, source="voice")

    [(text, markup)] = message.replies
    assert text == "📝 Filed to Study/Transformers/Attention as soft lookup.md"
    labels = [label for label, _ in _buttons(markup)]
    assert labels == ["📁 Study", "↩️ Back to inbox"]

    [edit] = await _tap(_buttons(markup)[1][1])
    assert edit == "↩️ Back in Voice Notes/Attention as soft lookup.md"
    assert (vault / "Voice Notes" / "Attention as soft lookup.md").exists()
    assert (vault / "Study" / "Transformers" / "_index.md").read_text() == ""
    assert (vault / log.LOG_NOTE).read_text().count("\n- ") == 3  # inbox, auto, back to inbox


@pytest.mark.asyncio
async def test_unsure_route_stays_in_inbox_and_asks(vault, monkeypatch):
    _route_to(monkeypatch, folder="Study", confidence=0.4, candidates=["Recipes"],
              new_folder="Study/Diffusion", reason="Could be study or cooking.")
    note = _inbox_note(vault)
    message = FakeMessage()
    await telegram.route_and_reply(message, note, transcript="…", hint=None, source="voice")

    [(text, markup)] = message.replies
    assert text == "📝 Saved to Voice Notes/2026-10-09 1432.md\nNot sure where it belongs — Could be study or cooking."
    buttons = _buttons(markup)
    assert [label for label, _ in buttons] == ["📁 Recipes", "🆕 New: Study/Diffusion", "Leave in inbox"]
    assert note.exists()

    [edit] = await _tap(buttons[1][1])
    assert edit == "📝 Filed to Study/Diffusion/Attention as soft lookup.md"
    assert (vault / "Study" / "Diffusion" / "_index.md").exists()

    assert await _tap(buttons[0][1]) == [f"That choice has expired — {log.LOG_NOTE} says where the note is."]


@pytest.mark.asyncio
async def test_router_failure_just_says_saved(vault, monkeypatch):
    def broken(template, params):
        raise RuntimeError("openrouter down")
    monkeypatch.setattr(router, "get_llm_response", broken)

    message = FakeMessage()
    note = _inbox_note(vault)
    await telegram.route_and_reply(message, note, transcript="…", hint=None, source="voice")
    assert message.replies == [("📝 Saved to Voice Notes/2026-10-09 1432.md", None)]
    assert note.exists()


@pytest.mark.asyncio
async def test_other_users_cannot_press_buttons(vault, monkeypatch):
    _route_to(monkeypatch, candidates=["Recipes"])
    message = FakeMessage()
    note = _inbox_note(vault)
    await telegram.route_and_reply(message, note, transcript="…", hint=None, source="voice")

    assert await _tap(_buttons(message.replies[0][1])[0][1], user_id=7) == []
    assert note.exists()
