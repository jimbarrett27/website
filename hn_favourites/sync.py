"""Scheduler hook: copy new Hacker News favourites into Readeck.

Readeck happily stores the same URL twice, so we remember which HN items we have
already sent (by item id) in a state file under :mod:`util.paths` and only send
the rest. Each id is recorded as soon as its bookmark is accepted, so a run that
dies halfway resumes where it stopped instead of duplicating the first half.

New favourites are sent oldest first, so Readeck's newest-first list ends up in
the same order as the HN favourites page.

As with the TRMNL panels, a missed run costs nothing -- the next one picks the
favourites up -- so failures are only reported once they persist, once, with a
single follow-up on recovery.
"""

import asyncio
import json
import logging
from pathlib import Path

from telegram.ext import ContextTypes

from hn_favourites import hn, readeck
from util.paths import data_path

logger = logging.getLogger(__name__)

HN_USERNAME = "jimjimjimmyjim"
REFRESH_INTERVAL_SECONDS = 60 * 60
# The first run walks the whole history; 40 pages is 1,200 favourites.
MAX_PAGES = 40
# Six consecutive failures at an hourly interval: favourites stalled for ~6 hours.
ALERT_AFTER_FAILURES = 6
FAILURES_KEY = "hn_favourites_consecutive_failures"


def state_file() -> Path:
    """HN item ids already sent to Readeck (see :mod:`util.paths`)."""
    return data_path("hn_favourites", "saved_ids.json")


def _load_saved() -> set[int]:
    path = state_file()
    return set(json.loads(path.read_text())) if path.exists() else set()


def _store_saved(saved: set[int]) -> None:
    path = state_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(sorted(saved)))


def sync() -> int:
    """Send unseen favourites to Readeck; return how many. Blocking; call off the event loop."""
    saved = _load_saved()
    fresh = hn.new_favourites(HN_USERNAME, saved, MAX_PAGES)
    for favourite in reversed(fresh):
        readeck.save_bookmark(favourite.url, favourite.title)
        saved.add(favourite.item_id)
        _store_saved(saved)
    return len(fresh)


async def hn_favourites_task(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Scheduler hook: sync HN favourites to Readeck in a worker thread."""
    failures = context.bot_data.get(FAILURES_KEY, 0)
    notify = context.bot_data["minecraft_bot"].send_message_to_me
    try:
        count = await asyncio.to_thread(sync)
    except Exception:
        failures += 1
        context.bot_data[FAILURES_KEY] = failures
        logger.exception("Failed to sync HN favourites to Readeck (%d in a row)", failures)
        if failures == ALERT_AFTER_FAILURES:
            notify(f"🔖 HN favourites → Readeck has failed {failures} times in a row")
        return

    context.bot_data[FAILURES_KEY] = 0
    logger.info("Saved %d new HN favourites to Readeck", count)
    if failures >= ALERT_AFTER_FAILURES:
        notify("🔖 HN favourites → Readeck is syncing again")
