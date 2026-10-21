"""Turn a recorded run back into something to watch."""

from pathlib import Path

import av
import numpy as np

from gb_agent.emulator import apply_event, boot

FPS = 60  # the Game Boy runs at ~59.73 fps; 60 is close enough to watch


def render_video(rom: bytes, start_state: bytes, events: list[dict], out_path: Path,
                 *, scale: int = 3) -> int:
    """Replay ``events`` from ``start_state`` and write every frame to an MP4.

    Ticks are replayed one frame at a time so each frame can be captured. The
    emulation is the same as ticking in bulk; only the rendered screen buffer in
    the save state differs, and no state is kept here. Returns the frame count.
    """
    pyboy = boot(rom, start_state)
    container = av.open(str(out_path), mode="w")
    try:
        stream = container.add_stream("h264", rate=FPS)
        stream.width = 160 * scale
        stream.height = 144 * scale
        stream.pix_fmt = "yuv420p"
        frames = 0
        for event in events:
            if event["type"] != "tick":
                apply_event(pyboy, event)
                continue
            for _ in range(event["frames"]):
                pyboy.tick(1, True)
                rgb = np.ascontiguousarray(pyboy.screen.ndarray[:, :, :3])
                big = rgb.repeat(scale, axis=0).repeat(scale, axis=1)
                container.mux(stream.encode(av.VideoFrame.from_ndarray(big, format="rgb24")))
                frames += 1
        container.mux(stream.encode())
        return frames
    finally:
        container.close()
        pyboy.stop(save=False)
