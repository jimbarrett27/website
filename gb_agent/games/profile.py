"""Everything game-specific, behind one dataclass.

The rest of gb_agent only knows about buttons, frames, the screen and memory, so
adding a game means writing a profile, not changing the harness. Whether the
cartridge has a clock (and so needs locking) is read from the ROM header, not
declared here.
"""

from dataclasses import dataclass, field
from pathlib import Path

from gb_agent.emulator import power_on_state


@dataclass(frozen=True)
class MemRef:
    """A labelled stretch of game memory."""

    addr: int
    length: int = 1
    bank: int | None = None


@dataclass(frozen=True)
class GameProfile:
    name: str
    rom: Path
    start_state: Path  # every run starts here; made from the ROM on first use
    watched_memory: dict[str, MemRef] = field(default_factory=dict)  # shown in traces
    progress_values: dict[str, MemRef] = field(default_factory=dict)  # logged every step
    seed_library: Path | None = None  # scripts copied into each new run's library
    notes: str = ""  # game facts given to the agent

    def rom_bytes(self) -> bytes:
        if not self.rom.exists():
            raise FileNotFoundError(f"no ROM for {self.name} at {self.rom}")
        return self.rom.read_bytes()

    def load_start_state(self) -> bytes:
        """The run start state, made (as a power-on state) the first time it's needed.

        It's made once and then kept: a fresh boot stamps the wall-clock time into
        the state, so regenerating it would give every later run a different start.
        """
        if not self.start_state.exists():
            self.start_state.parent.mkdir(parents=True, exist_ok=True)
            self.start_state.write_bytes(power_on_state(self.rom_bytes()))
        return self.start_state.read_bytes()
