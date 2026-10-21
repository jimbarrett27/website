"""Rendering a recorded run to video."""

import av

from gb_agent.emulator import RecordingGame, boot
from gb_agent.replay import render_video


def test_video_has_one_frame_per_game_frame(tmp_path, test_rom, test_start):
    game = RecordingGame(boot(test_rom, test_start))
    game.tick(20)
    game.tap("a", hold=3, after=17)
    out = tmp_path / "run.mp4"

    assert render_video(test_rom, test_start, game.events, out, scale=2) == 40

    with av.open(str(out)) as container:
        stream = container.streams.video[0]
        assert (stream.width, stream.height) == (320, 288)
        assert sum(1 for _ in container.decode(stream)) == 40
