"""``RecordingGame``: the only object agent scripts get to drive the game with.

Every call that changes the game is logged as an event, and replaying those
events from the same starting state reproduces the game exactly. Memory can be
read but not written. The underlying PyBoy is reachable if a script goes
looking for it; anything done that way isn't recorded, and the host's replay
check catches it.
"""

import io

from .core import BUTTONS, apply_event


class FrameLimitExceeded(Exception):
    """The script tried to advance more frames than this step allows."""


class EventLimitExceeded(Exception):
    """The script produced more input events than this step allows."""


class Memory:
    """Read-only view of the Game Boy's address space.

    ``memory[0xD20D]`` is one byte, ``memory[0xD000:0xD010]`` a list of bytes, and
    ``memory[bank, addr]`` (or a slice of addresses) reads a specific ROM/RAM bank.
    """

    def __init__(self, pyboy):
        self._memory = pyboy.memory

    def __getitem__(self, key):
        if isinstance(key, tuple):
            bank, addr = key
            if not isinstance(bank, int) or not isinstance(addr, (int, slice)):
                raise TypeError("memory[bank, addr]: bank must be an int, addr an int or slice")
        elif not isinstance(key, (int, slice)):
            raise TypeError("memory[addr]: addr must be an int or slice")
        value = self._memory[key]
        return list(value) if isinstance(value, (list, tuple, bytes, bytearray)) else value

    def u16(self, addr: int) -> int:
        """A little-endian 16-bit value."""
        return self._memory[addr] | (self._memory[addr + 1] << 8)

    def __setitem__(self, key, value):
        raise TypeError("game memory is read-only; the game only changes through inputs")


class RecordingGame:
    """Buttons, frames, screen and memory, with every input recorded.

    ``frame`` counts frames since the start of the run, so events from different
    steps line up on one timeline.
    """

    buttons = BUTTONS

    def __init__(self, pyboy, *, start_frame: int = 0, max_frames: int = 36_000,
                 max_events: int = 200_000):
        self._pyboy = pyboy
        self._max_frames = max_frames
        self._max_events = max_events
        self.start_frame = start_frame
        self.frame = start_frame
        self.events: list[dict] = []
        self.notes: list[dict] = []
        self.held: set[str] = set()
        self.memory = Memory(pyboy)
        self._after_tick = []  # callables run after every frame advance (see harness)

    @property
    def frames_used(self) -> int:
        return self.frame - self.start_frame

    def _record(self, event: dict) -> None:
        if len(self.events) >= self._max_events:
            raise EventLimitExceeded(f"more than {self._max_events} input events in one step")
        apply_event(self._pyboy, event)
        self.events.append(event)

    def _check_button(self, button: str) -> str:
        if button not in BUTTONS:
            raise ValueError(f"unknown button {button!r}; buttons are {', '.join(BUTTONS)}")
        return button

    def press(self, button: str) -> None:
        """Start holding ``button``. It stays held until ``release``."""
        self._record({"frame": self.frame, "type": "press", "button": self._check_button(button)})
        self.held.add(button)

    def release(self, button: str) -> None:
        self._record({"frame": self.frame, "type": "release", "button": self._check_button(button)})
        self.held.discard(button)

    def tick(self, frames: int = 1) -> None:
        """Advance the game ``frames`` frames (about 60 per second)."""
        if not isinstance(frames, int) or frames < 1:
            raise ValueError("frames must be a positive int")
        if self.frames_used + frames > self._max_frames:
            raise FrameLimitExceeded(
                f"advancing {frames} frames would pass this step's limit of {self._max_frames} "
                f"({self.frames_used} used)"
            )
        self._record({"frame": self.frame, "type": "tick", "frames": frames})
        self.frame += frames
        for hook in self._after_tick:
            hook()

    def tap(self, button: str, hold: int = 2, after: int = 6) -> None:
        """Press ``button`` for ``hold`` frames, release it, then wait ``after`` frames."""
        self.press(button)
        self.tick(hold)
        self.release(button)
        self.tick(after)

    def screenshot(self):
        """The current screen as a PIL image (160x144)."""
        return self._pyboy.screen.image.copy()

    def screenshot_png(self) -> bytes:
        buffer = io.BytesIO()
        self.screenshot().save(buffer, format="PNG")
        return buffer.getvalue()

    def note(self, label: str, value=None) -> None:
        """Record a labelled observation; it comes back with the step's result."""
        self.notes.append({"frame": self.frame, "label": str(label), "value": value})
