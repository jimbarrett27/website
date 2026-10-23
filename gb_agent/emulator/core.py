"""Booting PyBoy, save states, and applying recorded input events.

Determinism rules, measured on PyBoy 2.7 (see tests/gb_agent/test_emulator.py):

- The rendered screen is part of the save state, so a replay must make exactly
  the same ``tick`` calls as the original. Every frame advance renders, and
  ``apply_event`` is the one function that turns an event into PyBoy calls, for
  recording and replay alike.
- A fresh boot stamps the wall-clock time into the cartridge clock's state, so
  two boots never match byte for byte. Runs therefore always start from a saved
  state, never from a boot.
- The cartridge clock reads wall-clock time in compiled code. Locking it
  (``rtc_lock_experimental``) freezes it at its starting moment; the lock isn't
  saved in states, so ``load_state`` turns it back on every time.
"""

import io
import warnings

# PySDL2 warns on import that it's using its bundled SDL2. Harmless, but it would
# land in the stderr of every step the agent sees.
warnings.filterwarnings("ignore", message="Using SDL2 binaries", category=UserWarning)

from pyboy import PyBoy  # noqa: E402

BUTTONS = ("a", "b", "start", "select", "up", "down", "left", "right")

# Cartridge types with a real-time clock (MBC3+TIMER+BATTERY, MBC3+TIMER+RAM+BATTERY).
_RTC_CARTRIDGE_TYPES = {0x0F, 0x10}
_CARTRIDGE_TYPE_ADDR = 0x147


def has_rtc(rom: bytes) -> bool:
    return len(rom) > _CARTRIDGE_TYPE_ADDR and rom[_CARTRIDGE_TYPE_ADDR] in _RTC_CARTRIDGE_TYPES


def new_emulator(rom: bytes) -> PyBoy:
    """A headless, unthrottled PyBoy with its clock locked if it has one.

    The ROM goes in as bytes, not a path: given a path, PyBoy reads and writes
    battery-save and clock files next to the ROM.
    """
    pyboy = PyBoy(io.BytesIO(rom), window="null", sound_emulated=False)
    pyboy.set_emulation_speed(0)
    if has_rtc(rom):
        pyboy.rtc_lock_experimental(True)
    return pyboy


def save_state(pyboy: PyBoy) -> bytes:
    buffer = io.BytesIO()
    pyboy.save_state(buffer)
    return buffer.getvalue()


def load_state(pyboy: PyBoy, rom: bytes, state: bytes) -> None:
    pyboy.load_state(io.BytesIO(state))
    if has_rtc(rom):
        pyboy.rtc_lock_experimental(True)


def boot(rom: bytes, state: bytes) -> PyBoy:
    """An emulator at ``state``."""
    pyboy = new_emulator(rom)
    load_state(pyboy, rom, state)
    return pyboy


def power_on_state(rom: bytes) -> bytes:
    """The state of a freshly switched-on cartridge, before any frames.

    Every run starts from a saved state like this one, so it's made once and kept.
    """
    pyboy = new_emulator(rom)
    try:
        return save_state(pyboy)
    finally:
        pyboy.stop(save=False)


def apply_event(pyboy: PyBoy, event: dict) -> None:
    kind = event["type"]
    if kind == "tick":
        pyboy.tick(event["frames"], True)
    elif kind == "press":
        pyboy.button_press(event["button"])
    elif kind == "release":
        pyboy.button_release(event["button"])
    else:
        raise ValueError(f"unknown event type {kind!r}")


def apply_events(pyboy: PyBoy, events: list[dict]) -> int:
    """Apply ``events`` in order; return the number of frames advanced."""
    frames = 0
    for event in events:
        apply_event(pyboy, event)
        if event["type"] == "tick":
            frames += event["frames"]
    return frames
