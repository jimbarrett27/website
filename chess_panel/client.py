"""Read the ongoing Daily games between the two of us from chess.com.

chess.com's Published-Data API is public and read-only, so there is no key: one
GET of ``/pub/player/{username}/games`` returns every Daily game the player has
in progress, each with its FEN, PGN and move deadline. We filter that down to
games against the opponent.

The API asks for a ``User-Agent`` that says who is calling, and answers requests
without one more grudgingly; it also caches responses for a few minutes, which
is irrelevant at correspondence pace.
"""

import logging

import requests

from chess_panel.board import username_of

logger = logging.getLogger(__name__)

API_ROOT = "https://api.chess.com/pub"
USER_AGENT = "jimbarrett.dev TRMNL chess panel (+https://jimbarrett.dev)"
TIMEOUT_SECONDS = 30


def fetch_current_games(username: str) -> list[dict]:
    """Every Daily game ``username`` currently has in progress."""
    response = requests.get(
        f"{API_ROOT}/player/{username.lower()}/games",
        headers={"User-Agent": USER_AGENT},
        timeout=TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    return response.json().get("games", [])


def games_between(games: list[dict], player: str, opponent: str) -> list[dict]:
    """The standard-chess games in ``games`` played between exactly these two."""
    pair = {player.lower(), opponent.lower()}
    return [
        g for g in games
        if {username_of(g.get("white")), username_of(g.get("black"))} == pair
        and g.get("rules", "chess") == "chess"
    ]


def fetch_games_between(player: str, opponent: str) -> list[dict]:
    games = games_between(fetch_current_games(player), player, opponent)
    logger.info("%d ongoing game(s) between %s and %s", len(games), player, opponent)
    return games
