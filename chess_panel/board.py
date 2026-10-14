"""Reduce a chess.com Daily game to what one viewer's panel shows.

Pure, like :mod:`fitness.metrics`: :func:`build` takes the game dicts that
:mod:`chess_panel.client` returns, plus who is looking and what time it is, and
hands back a :class:`PanelState`. No network, no clock of its own.

Each player gets their own panel from the same game, so everything that depends
on the viewer is decided here: the board is flipped for whoever has Black, and
"your move" means the viewer's move. The template only draws.

The board goes over the wire as a 64-character string in *display* order --
top-left square first, already flipped -- with ``.`` for an empty square. The
template walks it with Liquid's ``slice``, so it never has to know about ranks,
files or orientation. 64 bytes is also comfortably inside TRMNL's 2KB payload,
which is what rules out sending a rendered board.
"""

import io
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

import chess
import chess.pgn

logger = logging.getLogger(__name__)

STOCKHOLM = ZoneInfo("Europe/Stockholm")
EMPTY = "."
NO_SQUARE = -1  # Liquid has no null worth comparing against


def username_of(player) -> str:
    """A player's username, from either shape chess.com uses.

    The current-games endpoint gives each side as a profile URL; the monthly
    archives give an object with a ``username``. Lower-cased, because chess.com
    usernames are case-insensitive and the API is not consistent about case.
    """
    if isinstance(player, dict):
        return player.get("username", "").lower()
    return str(player).rstrip("/").rsplit("/", 1)[-1].lower()


@dataclass
class PanelState:
    has_game: bool
    viewer: str
    opponent: str
    your_move: bool = False
    colour: str = ""            # the viewer's colour, "WHITE" or "BLACK"
    squares: str = ""           # 64 chars, display order, "." for empty
    files: str = "abcdefgh"     # left to right, as displayed
    ranks: str = "87654321"     # top to bottom, as displayed
    last_from: int = NO_SQUARE  # display index of the last move's squares
    last_to: int = NO_SQUARE
    last_move: str = ""         # e.g. "23. Nf3" or "23... Nf6"
    move_number: int = 0
    deadline: str = ""          # e.g. "2D 4H LEFT"
    deadline_at: str = ""       # e.g. "THU 14:30"
    other_games: int = 0
    url: str = ""
    updated: str = ""

    def as_merge_variables(self) -> dict:
        return asdict(self)


def _display_index(square: chess.Square, flipped: bool) -> int:
    """Where a square lands in the display-order string."""
    row = 7 - chess.square_rank(square)
    col = chess.square_file(square)
    if flipped:
        row, col = 7 - row, 7 - col
    return row * 8 + col


def _squares(board: chess.Board, flipped: bool) -> str:
    cells = [EMPTY] * 64
    for square, piece in board.piece_map().items():
        cells[_display_index(square, flipped)] = piece.symbol()
    return "".join(cells)


def _last_move(pgn: str) -> tuple[chess.Move, str] | None:
    """The final move of the PGN and its numbered SAN, or None before move one."""
    game = chess.pgn.read_game(io.StringIO(pgn)) if pgn else None
    if game is None or game.end() is game:
        return None
    end = game.end()
    before = end.parent.board()
    number = before.fullmove_number
    prefix = f"{number}." if before.turn == chess.WHITE else f"{number}..."
    return end.move, f"{prefix} {before.san(end.move)}"


def _time_left(move_by: int, now: datetime) -> tuple[str, str]:
    """Countdown and wall-clock deadline for the player to move.

    chess.com sends 0 when there is no deadline to show (e.g. a vacation is
    running), so that comes back as blanks rather than a time in 1970.
    """
    if not move_by:
        return "", ""
    deadline = datetime.fromtimestamp(move_by, tz=STOCKHOLM)
    minutes = max(0, int((deadline - now).total_seconds() // 60))
    days, rem = divmod(minutes, 24 * 60)
    hours, mins = divmod(rem, 60)
    if days:
        left = f"{days}D {hours}H LEFT"
    elif hours:
        left = f"{hours}H {mins}M LEFT"
    else:
        left = f"{mins}M LEFT"
    return left, deadline.strftime("%a %H:%M").upper()


def pick_game(games: list[dict]) -> dict | None:
    """The game to show when there are several.

    Most recently active, so the panel follows whichever game is actually being
    played, and both players' panels agree on which one that is.
    """
    return max(games, key=lambda g: g.get("last_activity", 0), default=None)


def build(games: list[dict], viewer: str, opponent: str, now: datetime) -> PanelState:
    """The panel ``viewer`` should see, given the ongoing games between the two."""
    viewer, opponent = viewer.lower(), opponent.lower()
    updated = now.astimezone(STOCKHOLM).strftime("%H:%M")
    game = pick_game(games)
    if game is None:
        return PanelState(has_game=False, viewer=viewer, opponent=opponent, updated=updated)

    viewer_colour = chess.WHITE if username_of(game.get("white")) == viewer else chess.BLACK
    flipped = viewer_colour == chess.BLACK
    # The FEN is the authority on the position; the PGN is only read for the
    # last move, so a PGN we fail to parse costs the highlight, not the board.
    board = chess.Board(game["fen"])

    state = PanelState(
        has_game=True,
        viewer=viewer,
        opponent=opponent,
        your_move=board.turn == viewer_colour,
        colour="WHITE" if viewer_colour == chess.WHITE else "BLACK",
        squares=_squares(board, flipped),
        files="hgfedcba" if flipped else "abcdefgh",
        ranks="12345678" if flipped else "87654321",
        move_number=board.fullmove_number,
        other_games=len(games) - 1,
        url=game.get("url", ""),
        updated=updated,
    )
    state.deadline, state.deadline_at = _time_left(game.get("move_by", 0), now)

    try:
        last = _last_move(game.get("pgn", ""))
    except Exception:
        logger.exception("could not read the last move from the PGN of %s", state.url)
        last = None
    if last is not None:
        move, state.last_move = last
        state.last_from = _display_index(move.from_square, flipped)
        state.last_to = _display_index(move.to_square, flipped)
    return state
