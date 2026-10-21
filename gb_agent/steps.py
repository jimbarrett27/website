"""One step: run a script against the game in the sandbox, then check the record.

A step starts from a save state, runs the script in a fresh container with
``game`` (a ``RecordingGame``) in scope, and comes back with the new state and
every input the script made. The host then replays those inputs from the
starting state on its own emulator and compares the result with the state the
sandbox produced. They match unless something changed the game without being
recorded -- a script reaching past ``RecordingGame`` to press buttons or write
memory -- and then the step is marked unverified.

Replaying runs no agent code, only recorded inputs into a trusted ROM, so it's
safe to do on the host. The inputs themselves come out of the sandbox, though,
so they're validated before they're replayed.
"""

import base64
from dataclasses import dataclass, field
from pathlib import Path

from gb_agent.emulator import BUTTONS, apply_events, boot, save_state
from gb_agent.sandbox import SandboxLimits, SandboxResult, run_in_sandbox

HARNESS = "gb_agent.emulator.harness"
ROM_IN_SANDBOX = "/rom/game.gb"


@dataclass(frozen=True)
class StepLimits:
    max_frames: int = 36_000  # ten minutes of game time
    max_events: int = 200_000
    sandbox: SandboxLimits = SandboxLimits()


@dataclass
class StepOutcome:
    sandbox: SandboxResult
    start_frame: int
    end_frame: int
    state: bytes | None  # None: the step produced nothing usable; keep the old state
    events: list[dict] = field(default_factory=list)
    notes: list[dict] = field(default_factory=list)
    screenshot_png: bytes | None = None
    verified: bool = False  # replaying the events reproduced the state exactly
    problem: str = ""  # why there's no state, or why it isn't verified

    @property
    def usable(self) -> bool:
        return self.state is not None and self.verified

    @property
    def frames_used(self) -> int:
        return self.end_frame - self.start_frame


def validate_events(events, start_frame: int, end_frame: int, limits: StepLimits) -> str:
    """Why ``events`` can't be replayed safely, or "" if they can."""
    if not isinstance(events, list):
        return "events is not a list"
    if len(events) > limits.max_events:
        return f"{len(events)} events, over the limit of {limits.max_events}"
    frame = start_frame
    for i, event in enumerate(events):
        if not isinstance(event, dict) or event.get("frame") != frame:
            return f"event {i} is malformed or out of order: {event!r}"
        kind = event.get("type")
        if kind == "tick":
            frames = event.get("frames")
            if type(frames) is not int or frames < 1:
                return f"event {i} has a bad frame count: {event!r}"
            frame += frames
            if frame - start_frame > limits.max_frames:
                return f"events advance more than the limit of {limits.max_frames} frames"
        elif kind in ("press", "release"):
            if event.get("button") not in BUTTONS:
                return f"event {i} has an unknown button: {event!r}"
        else:
            return f"event {i} has an unknown type: {event!r}"
        if set(event) - {"frame", "type", "frames", "button"}:
            return f"event {i} has unexpected fields: {event!r}"
    if frame != end_frame:
        return f"events end at frame {frame}, but the step reported {end_frame}"
    return ""


def replay(rom: bytes, start_state: bytes, events: list[dict]) -> bytes:
    """The state reached by applying ``events`` from ``start_state``."""
    pyboy = boot(rom, start_state)
    try:
        apply_events(pyboy, events)
        return save_state(pyboy)
    finally:
        pyboy.stop(save=False)


def run_step(
    rom_path: Path,
    state: bytes,
    code: str,
    *,
    start_frame: int = 0,
    limits: StepLimits = StepLimits(),
    image: str | None = None,
) -> StepOutcome:
    """Run ``code`` against the game at ``state`` in the sandbox, and check it."""
    payload = {
        "rom": ROM_IN_SANDBOX,
        "state": base64.b64encode(state).decode(),
        "start_frame": start_frame,
        "max_frames": limits.max_frames,
        "max_events": limits.max_events,
    }
    result = run_in_sandbox(
        code, payload,
        limits=limits.sandbox,
        read_only_mounts={Path(rom_path): ROM_IN_SANDBOX},
        harness=HARNESS,
        image=image,
    )
    outcome = StepOutcome(sandbox=result, start_frame=start_frame,
                          end_frame=start_frame, state=None)
    h = result.harness
    if h is None:
        if result.harness_error:
            outcome.problem = f"harness failed: {result.harness_error['message']}"
        else:
            outcome.problem = f"no result from the sandbox ({result.status}: {result.detail})"
        return outcome

    try:
        new_state = base64.b64decode(h["state"], validate=True)
        end_frame = h["end_frame"]
        screenshot = base64.b64decode(h["screenshot"], validate=True)
    except (KeyError, TypeError, ValueError) as e:
        outcome.problem = f"malformed step result: {e}"
        return outcome
    if type(end_frame) is not int:
        outcome.problem = "malformed step result: end_frame is not an int"
        return outcome
    if problem := validate_events(h.get("events"), start_frame, end_frame, limits):
        outcome.problem = f"events rejected: {problem}"
        return outcome

    outcome.end_frame = end_frame
    outcome.state = new_state
    outcome.events = h["events"]
    outcome.notes = h.get("notes") or []
    outcome.screenshot_png = screenshot
    outcome.verified = replay(Path(rom_path).read_bytes(), state, outcome.events) == new_state
    if not outcome.verified:
        outcome.problem = ("replaying the recorded inputs didn't reproduce the step's state: "
                           "something changed the game without going through `game`")
    return outcome
