"""Game profiles, keyed by name."""

from gb_agent.games.profile import GameProfile, MemRef
from gb_agent.games.silver import SILVER

GAMES: dict[str, GameProfile] = {SILVER.name: SILVER}

__all__ = ["GAMES", "GameProfile", "MemRef", "SILVER"]
