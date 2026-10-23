"""Game profiles: setup inputs and start states."""

import pytest

from gb_agent.emulator import RecordingGame, apply_events, boot, save_state
from gb_agent.games import SILVER, GameProfile
from gb_agent.games.profile import apply_setup
from tests.gb_agent.conftest import TEST_ROM


def test_setup_commands(test_rom, test_start):
    game = RecordingGame(boot(test_rom, test_start))
    apply_setup(game, ("t:10", "a", "start:3:5"))
    assert game.events == [
        {"frame": 0, "type": "tick", "frames": 10},
        {"frame": 10, "type": "press", "button": "a"},
        {"frame": 10, "type": "tick", "frames": 2},
        {"frame": 12, "type": "release", "button": "a"},
        {"frame": 12, "type": "tick", "frames": 6},
        {"frame": 18, "type": "press", "button": "start"},
        {"frame": 18, "type": "tick", "frames": 3},
        {"frame": 21, "type": "release", "button": "start"},
        {"frame": 21, "type": "tick", "frames": 5},
    ]


@pytest.mark.parametrize("bad", ["t", "t:1:2", "a:1", "turbo"])
def test_bad_setup_commands_are_rejected(test_rom, test_start, bad):
    with pytest.raises(ValueError):
        apply_setup(RecordingGame(boot(test_rom, test_start)), (bad,))


def test_start_state_is_power_on_plus_setup_and_is_kept(tmp_path, test_rom):
    profile = GameProfile(
        name="test",
        rom=TEST_ROM,
        power_on_state=tmp_path / "states" / "power_on.state",
        start_state=tmp_path / "states" / "start.state",
        setup=("t:30", "a"),
    )
    start = profile.load_start_state()

    power_on = profile.power_on_state.read_bytes()
    replayed = RecordingGame(boot(test_rom, power_on))
    apply_setup(replayed, profile.setup)
    assert save_state(replayed._pyboy) == start

    # Kept, not remade: a remade power-on state would differ in its clock stamp.
    mtime = profile.start_state.stat().st_mtime_ns
    assert profile.load_start_state() == start
    assert profile.start_state.stat().st_mtime_ns == mtime


def test_silver_starts_in_control(silver_rom):
    """From the bedroom start, walking left moves the view (the player has control)."""
    start = SILVER.load_start_state()
    still = RecordingGame(boot(silver_rom, start))
    still.tick(60)
    walked = RecordingGame(boot(silver_rom, start))
    walked.tap("left", hold=8, after=52)
    assert walked.screenshot().tobytes() != still.screenshot().tobytes()

    replay = boot(silver_rom, start)
    apply_events(replay, walked.events)
    assert save_state(replay) == save_state(walked._pyboy)
