"""Scheduler hook for pushing the chess panels to TRMNL.

Correspondence moves land whenever either of us gets round to them, so like the
fitness panel this refreshes on a fixed interval rather than at chosen times. A
move then reaches the wall within ``REFRESH_INTERVAL_SECONDS`` plus the device's
own refresh, which is plenty at a pace of days per move -- and four pushes an
hour per plugin is well inside TRMNL's twelve.

As with fitness, a missed push only costs a stale panel and the next run is the
retry, so failures are reported once they persist for ``ALERT_AFTER_FAILURES``
runs in a row, once, with a single follow-up on recovery.
"""

import asyncio
import logging

from telegram.ext import ContextTypes

from chess_panel import trmnl

logger = logging.getLogger(__name__)

REFRESH_INTERVAL_SECONDS = 15 * 60
# Eight consecutive failures at a 15-minute interval: about two hours stale.
ALERT_AFTER_FAILURES = 8
FAILURES_KEY = "chess_panel_consecutive_failures"


def refresh_panels() -> bool:
    """Fetch the games and push both panels. Blocking; call off the event loop."""
    return trmnl.push(trmnl.panels())


async def chess_panel_task(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Scheduler hook: refresh the TRMNL chess panels in a worker thread."""
    failures = context.bot_data.get(FAILURES_KEY, 0)
    notify = context.bot_data["minecraft_bot"].send_message_to_me
    try:
        if not await asyncio.to_thread(refresh_panels):
            raise RuntimeError("TRMNL rejected a push")
    except Exception:
        failures += 1
        context.bot_data[FAILURES_KEY] = failures
        logger.exception("Failed to refresh TRMNL chess panels (%d in a row)", failures)
        if failures == ALERT_AFTER_FAILURES:
            notify(f"♟️ TRMNL chess panel has failed {failures} times in a row — panel is stale")
        return

    context.bot_data[FAILURES_KEY] = 0
    logger.info("TRMNL chess panels refreshed")
    if failures >= ALERT_AFTER_FAILURES:
        notify("♟️ TRMNL chess panel is updating again")
