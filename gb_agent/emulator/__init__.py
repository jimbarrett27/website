"""Everything that touches PyBoy directly.

Shared by the sandbox (where scripts drive the game) and the host (where steps are
replayed and checked), so both run the same code. It's copied into the sandbox
image, which is why it imports nothing but the standard library, PyBoy and itself.
"""

from .core import (
    BUTTONS,
    apply_event,
    apply_events,
    boot,
    has_rtc,
    load_state,
    new_emulator,
    power_on_state,
    save_state,
)
from .recording import EventLimitExceeded, FrameLimitExceeded, Memory, RecordingGame

__all__ = [
    "BUTTONS",
    "EventLimitExceeded",
    "FrameLimitExceeded",
    "Memory",
    "RecordingGame",
    "apply_event",
    "apply_events",
    "boot",
    "has_rtc",
    "load_state",
    "new_emulator",
    "power_on_state",
    "save_state",
]
