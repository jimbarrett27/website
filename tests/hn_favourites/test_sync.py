"""Tests for hn_favourites.sync -- dedup, resume after failure, and alert-once."""

import asyncio
from unittest.mock import MagicMock

import pytest

from hn_favourites import sync
from hn_favourites.hn import Favourite


@pytest.fixture(autouse=True)
def data_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("JIMBARRETT_DATA_DIR", str(tmp_path))


def _fav(item_id):
    return Favourite(item_id, f"https://example.com/{item_id}", str(item_id))


@pytest.fixture
def hn_favourites(monkeypatch):
    """HN shows favourites 3, 2, 1 (newest first); honour the ``seen`` set."""
    favourites = [_fav(3), _fav(2), _fav(1)]
    monkeypatch.setattr(
        sync.hn, "new_favourites",
        lambda user, seen, max_pages: [f for f in favourites if f.item_id not in seen],
    )


@pytest.fixture
def saved(monkeypatch):
    urls = []
    monkeypatch.setattr(sync.readeck, "save_bookmark", lambda url, title: urls.append(url))
    return urls


def test_sends_oldest_first(hn_favourites, saved):
    assert sync.sync() == 3
    assert saved == [f"https://example.com/{i}" for i in (1, 2, 3)]


def test_second_run_sends_nothing(hn_favourites, saved):
    sync.sync()
    assert sync.sync() == 0
    assert len(saved) == 3


def test_failure_midway_keeps_what_was_saved(hn_favourites, monkeypatch):
    sent = []

    def flaky(url, title):
        if url.endswith("/2"):
            raise RuntimeError("readeck down")
        sent.append(url)

    monkeypatch.setattr(sync.readeck, "save_bookmark", flaky)
    with pytest.raises(RuntimeError):
        sync.sync()
    assert sync._load_saved() == {1}

    monkeypatch.setattr(sync.readeck, "save_bookmark", lambda url, title: sent.append(url))
    assert sync.sync() == 2
    assert sent == [f"https://example.com/{i}" for i in (1, 2, 3)]


@pytest.fixture
def context():
    ctx = MagicMock()
    ctx.bot_data = {"minecraft_bot": MagicMock()}
    return ctx


def _run(context, monkeypatch, outcomes):
    """Run the job once per outcome: an int is a successful sync, an exception raises."""
    for outcome in outcomes:
        def fake_sync(outcome=outcome):
            if isinstance(outcome, Exception):
                raise outcome
            return outcome
        monkeypatch.setattr(sync, "sync", fake_sync)
        asyncio.run(sync.hn_favourites_task(context))
    return [c.args[0] for c in context.bot_data["minecraft_bot"].send_message_to_me.call_args_list]


def test_success_is_silent(context, monkeypatch):
    assert _run(context, monkeypatch, [3, 0]) == []


def test_brief_outage_is_silent(context, monkeypatch):
    outcomes = [RuntimeError("x")] * (sync.ALERT_AFTER_FAILURES - 1) + [0]
    assert _run(context, monkeypatch, outcomes) == []


def test_sustained_outage_alerts_once_then_recovers(context, monkeypatch):
    outcomes = [RuntimeError("HN down")] * (sync.ALERT_AFTER_FAILURES + 3) + [0, 0]
    messages = _run(context, monkeypatch, outcomes)
    assert len(messages) == 2
    assert "failed" in messages[0]
    assert "syncing again" in messages[1]
