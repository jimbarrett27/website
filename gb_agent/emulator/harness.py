"""The game side of one step, run inside the sandbox by the runner.

The runner constructs ``Harness(payload)`` before the script, puts ``scope()``
into the script's globals, and calls ``finish()`` afterwards, whether or not the
script raised. Payload:

    {"rom": path, "state": base64, "start_frame": int,
     "max_frames": int, "max_events": int,
     "watch": {label: [addr, length, bank or null]},   # optional
     "keyframe_every": int, "max_keyframes": int}       # optional

Besides the new state and the events, it reports what's needed to show the
agent what happened: the screen before and after, a few keyframes in between,
and the watched memory before and after.
"""

import base64

from .core import boot, save_state
from .recording import RecordingGame


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode()


class Harness:
    def __init__(self, payload: dict):
        with open(payload["rom"], "rb") as f:
            rom = f.read()
        self._pyboy = boot(rom, base64.b64decode(payload["state"]))
        self.game = RecordingGame(
            self._pyboy,
            start_frame=payload["start_frame"],
            max_frames=payload["max_frames"],
            max_events=payload["max_events"],
        )
        self._watch = payload.get("watch") or {}
        self._keyframe_every = payload.get("keyframe_every") or 0
        self._max_keyframes = payload.get("max_keyframes") or 0
        self._keyframes: list[tuple[int, bytes]] = []
        self._next_keyframe = self.game.frame + self._keyframe_every

        # Saved states include the last rendered screen, so this is what was showing.
        self._before_png = self.game.screenshot_png()
        self._watch_before = self._read_watch()
        if self._keyframe_every:
            self.game._after_tick.append(self._maybe_keyframe)

    def _read_watch(self) -> dict:
        values = {}
        for label, (addr, length, bank) in self._watch.items():
            if bank is None:
                values[label] = [self.game.memory[a] for a in range(addr, addr + length)]
            else:
                values[label] = [self.game.memory[bank, a] for a in range(addr, addr + length)]
        return values

    def _maybe_keyframe(self) -> None:
        if self.game.frame >= self._next_keyframe:
            self._keyframes.append((self.game.frame, self.game.screenshot_png()))
            self._next_keyframe = self.game.frame + self._keyframe_every

    def _chosen_keyframes(self) -> list[tuple[int, bytes]]:
        """At most ``max_keyframes``, spread evenly, never the final frame twice."""
        frames = [k for k in self._keyframes if k[0] != self.game.frame]
        if len(frames) <= self._max_keyframes:
            return frames
        if self._max_keyframes <= 0:
            return []
        step = len(frames) / self._max_keyframes
        return [frames[int(i * step)] for i in range(self._max_keyframes)]

    def scope(self) -> dict:
        return {"game": self.game}

    def finish(self) -> dict:
        game = self.game
        try:
            game.end_step()
        except Exception:
            pass  # e.g. the event limit; the replay check still guards the record
        return {
            "state": _b64(save_state(self._pyboy)),
            "events": game.events,
            "start_frame": game.start_frame,
            "end_frame": game.frame,
            "notes": game.notes,
            "screenshot": _b64(game.screenshot_png()),
            "before_screenshot": _b64(self._before_png),
            "keyframes": [[frame, _b64(png)] for frame, png in self._chosen_keyframes()],
            "watch_before": self._watch_before,
            "watch_after": self._read_watch(),
        }
