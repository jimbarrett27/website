"""Pokemon Silver (USA, Europe).

The ROM isn't in the repo; it lives at ``<data dir>/gb_agent/roms/``. The clock
is locked from power-on, so in-game time never moves: it stays at whatever time
is set when a new game is started.

Memory addresses are added as they're checked against the running game, not
copied from a disassembly (Gold/Silver addresses differ from Crystal's).
"""

from util.paths import data_path

from gb_agent.games.profile import GameProfile

SILVER = GameProfile(
    name="silver",
    rom=data_path("gb_agent", "roms", "pokemon_silver.gbc"),
    start_state=data_path("gb_agent", "states", "silver_power_on.state"),
    notes="Pokemon Silver for the Game Boy Color. The game starts from power-on.",
)
