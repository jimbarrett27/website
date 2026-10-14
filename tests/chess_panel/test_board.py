"""Tests for chess_panel.board and the filtering in chess_panel.client.

The fixture is synthetic, in the documented shape of chess.com's current-games
endpoint (sides as profile URLs, PGN with headers), because there was no live
Daily game to record when this was written. Replace it with a real response once
there is one.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from chess_panel.board import EMPTY, NO_SQUARE, build, username_of
from chess_panel.client import games_between
from util import trmnl

FIXTURE = Path(__file__).parent / "fixtures" / "current_games.json"
ME, FRIEND = "jimjimjimmyjim", "naslundx"
# A day, five hours and twenty minutes before the fixture's move_by.
NOW = datetime.fromtimestamp(1792411200 - (29 * 60 + 20) * 60, tz=timezone.utc)


@pytest.fixture
def games():
    return games_between(json.loads(FIXTURE.read_text())["games"], ME, FRIEND)


def test_username_from_either_shape():
    assert username_of("https://api.chess.com/pub/player/NaslundX") == "naslundx"
    assert username_of({"username": "JimJimJimmyJim", "rating": 1200}) == "jimjimjimmyjim"


def test_games_between_drops_other_opponents(games):
    assert len(games) == 2
    assert all("someoneelse" not in g["black"] for g in games)


def test_most_recent_game_is_shown(games):
    state = build(games, ME, FRIEND, NOW)
    assert state.url.endswith("900000001")
    assert state.other_games == 1


def test_white_viewer_sees_board_unflipped(games):
    state = build(games, ME, FRIEND, NOW)
    assert state.colour == "WHITE"
    assert state.your_move
    assert state.files == "abcdefgh" and state.ranks == "87654321"
    # Top-left is a8 (empty), g8 holds Black's king, b1 White's.
    assert state.squares[0] == EMPTY
    assert state.squares[6] == "k"
    assert state.squares[7 * 8 + 1] == "K"


def test_black_viewer_sees_board_flipped(games):
    white = build(games, ME, FRIEND, NOW)
    black = build(games, FRIEND, ME, NOW)
    assert black.colour == "BLACK"
    assert not black.your_move
    assert black.files == "hgfedcba" and black.ranks == "12345678"
    assert black.squares == white.squares[::-1]


def test_last_move_is_numbered_and_highlighted(games):
    white = build(games, ME, FRIEND, NOW)
    black = build(games, FRIEND, ME, NOW)
    # ...Rb8 was Black's 17th move, a8 -> b8.
    assert white.last_move == "17... Rb8"
    assert white.move_number == 18
    assert (white.last_from, white.last_to) == (0, 1)
    assert (black.last_from, black.last_to) == (63, 62)


def test_deadline(games):
    state = build(games, ME, FRIEND, NOW)
    assert state.deadline == "1D 5H LEFT"
    assert state.deadline_at == "MON 14:00"  # 12:00 UTC, in CEST


def test_no_game(games):
    state = build([], ME, FRIEND, NOW)
    assert not state.has_game
    assert state.opponent == FRIEND


def test_unreadable_pgn_still_draws_the_board(games):
    games = [{**g, "pgn": "not a pgn {{{"} for g in games]
    state = build(games, ME, FRIEND, NOW)
    assert state.squares[6] == "k"
    assert state.last_from == NO_SQUARE and state.last_move == ""


def test_payload_fits(games):
    for viewer, opponent in [(ME, FRIEND), (FRIEND, ME)]:
        trmnl.build_payload(build(games, viewer, opponent, NOW).as_merge_variables())
