"""The game side of one step, run inside the sandbox by the runner.

The runner constructs ``Harness(payload)`` before the script, puts ``scope()``
into the script's globals, and calls ``finish()`` afterwards, whether or not the
script raised. Payload:

    {"rom": path, "state": base64, "start_frame": int,
     "max_frames": int, "max_events": int}
"""

import base64

from .core import boot, save_state
from .recording import RecordingGame


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

    def scope(self) -> dict:
        return {"game": self.game}

    def finish(self) -> dict:
        game = self.game
        return {
            "state": base64.b64encode(save_state(self._pyboy)).decode(),
            "events": game.events,
            "start_frame": game.start_frame,
            "end_frame": game.frame,
            "notes": game.notes,
            "screenshot": base64.b64encode(game.screenshot_png()).decode(),
        }
