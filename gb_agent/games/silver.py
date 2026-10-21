"""Pokemon Silver (USA, Europe).

The ROM isn't in the repo; it lives at ``<data dir>/gb_agent/roms/``.

Runs start in the player's bedroom, just after new-game setup. ``SETUP`` is the
input sequence that gets there from power-on, played once by hand (2026-10-21,
watching screenshots) and recorded:

- title screen, NEW GAME
- the clock: left at its default, 10:00, then 0 minutes. The cartridge clock is
  locked, so in-game time stays 10:00 (daytime) for good.
- Professor Oak's introduction; the player's name is the first preset, SILVER
- ends at frame 7452, standing in the bedroom with control

The day of the week isn't set yet; Mom asks downstairs.

Memory addresses are added as they're checked against the running game, not
copied from a disassembly (Gold/Silver addresses differ from Crystal's).
"""

from util.paths import data_path

from gb_agent.games.profile import GameProfile

_A = "a:4:100"

SETUP = (
    "t:720", "start:4:60", "start:4:60", "a:4:120",  # title screen, NEW GAME
    "t:120", "a:4:90", "t:60", *["a:4:90"] * 8,  # wake-up call; clock at 10:00, 0 min
    "t:120", *[_A] * 17,  # Oak's introduction
    "t:90", *[_A] * 11,
    "down:4:20", _A,  # name: the first preset, SILVER
    "t:60", *[_A] * 5,
    "t:200", *[_A] * 3,
    "t:200", _A, _A,
    "t:300", _A,
    "t:300",  # into the bedroom
)

SILVER = GameProfile(
    name="silver",
    rom=data_path("gb_agent", "roms", "pokemon_silver.gbc"),
    power_on_state=data_path("gb_agent", "states", "silver_power_on.state"),
    start_state=data_path("gb_agent", "states", "silver_bedroom.state"),
    setup=SETUP,
    notes=(
        "Pokemon Silver for the Game Boy Color. You are SILVER, starting in your "
        "bedroom upstairs at home in New Bark Town. The in-game time is always 10:00."
    ),
)
