"""Render the chess panel locally. See :mod:`util.panel_preview`.

    uv run --extra dev python -m chess_panel.preview                  # live games, my side
    uv run --extra dev python -m chess_panel.preview --as naslundx    # live games, his side
    uv run --extra dev python -m chess_panel.preview --games tests/chess_panel/fixtures/current_games.json

``--games`` takes a saved ``/pub/player/{username}/games`` response instead of
reading chess.com, for designing against a position when no game is on.
"""

import argparse
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from chess_panel.board import build
from chess_panel.client import fetch_games_between, games_between
from chess_panel.trmnl import PLAYERS
from util import panel_preview, trmnl

TEMPLATE = Path(__file__).parent / "templates" / "chess_full.liquid"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("panel-preview/chess"))
    parser.add_argument("--as", dest="viewer", choices=PLAYERS, default=PLAYERS[0],
                        help="whose panel to render")
    parser.add_argument("--games", type=Path, help="a saved current-games response to use")
    parser.add_argument("--json", type=Path, help="also write the webhook payload here")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    opponent = next(p for p in PLAYERS if p != args.viewer)
    if args.games:
        games = games_between(json.loads(args.games.read_text())["games"], args.viewer, opponent)
    else:
        games = fetch_games_between(args.viewer, opponent)

    merge_variables = build(games, args.viewer, opponent, datetime.now(timezone.utc)).as_merge_variables()
    payload = trmnl.build_payload(merge_variables)
    if args.json:
        args.json.write_text(payload)
    panel_preview.preview(TEMPLATE, merge_variables, args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
