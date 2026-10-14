"""Push the chess panel to both players' TRMNL private plugins.

One chess.com read, then one push per player, each with the board from their own
side. The panel's markup lives in ``chess_panel/templates/chess_full.liquid``;
both plugins paste the same file, so keep it the source of truth.

A player whose webhook secret doesn't exist yet is skipped with a warning rather
than failing the run, so one panel can go live before the other is set up.

Push one manually::

    uv run python -m chess_panel.trmnl            # push live games
    uv run python -m chess_panel.trmnl --dry-run  # print the payloads, send nothing
"""

import argparse
import logging
from datetime import datetime, timezone

from google.api_core.exceptions import NotFound

from chess_panel.board import PanelState, build
from chess_panel.client import fetch_games_between
from gcp_util.secrets import get_trmnl_chess_webhook_url
from util import trmnl

logger = logging.getLogger(__name__)

# Each player sees the other as the opponent; the game list is the same either way.
PLAYERS = ("jimjimjimmyjim", "naslundx")


def panels(now: datetime | None = None) -> list[PanelState]:
    """One panel per player, from a single read of the ongoing games."""
    now = now or datetime.now(timezone.utc)
    me, friend = PLAYERS
    games = fetch_games_between(me, friend)
    return [build(games, me, friend, now), build(games, friend, me, now)]


def push(states: list[PanelState]) -> bool:
    """Push each player's panel. Returns whether every configured push landed."""
    ok = True
    for state in states:
        try:
            webhook = get_trmnl_chess_webhook_url(state.viewer)
        except NotFound:
            logger.warning("no webhook secret for %s yet; skipping their panel", state.viewer)
            continue
        ok = trmnl.push(webhook, state.as_merge_variables()) and ok
    return ok


def main() -> int:
    parser = argparse.ArgumentParser(description="Push the chess panels to TRMNL.")
    parser.add_argument("--dry-run", action="store_true",
                        help="print the payloads without sending them")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    states = panels()
    if args.dry_run:
        for state in states:
            print(trmnl.build_payload(state.as_merge_variables()))
        return 0
    return 0 if push(states) else 1


if __name__ == "__main__":
    raise SystemExit(main())
