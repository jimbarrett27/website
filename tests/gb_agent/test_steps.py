"""Steps run in the real sandbox, and the host's replay check on what comes back."""

import base64

import pytest

from gb_agent.emulator import apply_events, boot, save_state
from gb_agent.sandbox import SandboxLimits
from gb_agent.steps import StepLimits, replay, run_step, validate_events
from tests.gb_agent.conftest import TEST_ROM, needs_docker

QUICK = StepLimits(sandbox=SandboxLimits(timeout_s=20))


def step(image, state, code, **kwargs):
    kwargs.setdefault("limits", QUICK)
    return run_step(TEST_ROM, state, code, image=image, **kwargs)


pytestmark = needs_docker


def test_a_step_runs_and_verifies(image, test_rom, test_start):
    code = (
        "for _ in range(5):\n"
        "    game.tap('a', hold=3, after=10)\n"
        "game.note('done', game.frame)\n"
        "result = len(game.events)\n"
    )
    outcome = step(image, test_start, code)
    assert outcome.sandbox.status == "ok", outcome.sandbox
    assert outcome.usable, outcome.problem
    assert outcome.frames_used == 65
    assert outcome.sandbox.value == len(outcome.events) == 20
    assert outcome.notes == [{"frame": 65, "label": "done", "value": 65}]
    assert outcome.screenshot_png.startswith(b"\x89PNG")


def test_sandbox_and_host_agree_exactly(image, test_rom, test_start):
    outcome = step(image, test_start, "game.tap('start')\ngame.tick(200)")
    host = boot(test_rom, test_start)
    apply_events(host, outcome.events)
    assert save_state(host) == outcome.state


def test_steps_chain_and_replay_from_the_run_start(image, test_rom, test_start):
    first = step(image, test_start, "game.tap('a', after=30)")
    second = step(image, first.state, "game.tap('b', after=30)", start_frame=first.end_frame)
    assert first.usable and second.usable
    assert second.events[0]["frame"] == first.end_frame
    assert replay(test_rom, test_start, first.events + second.events) == second.state


def test_pressing_buttons_behind_games_back_is_caught(image, test_start):
    code = "game._pyboy.button_press('start')\ngame.tick(60)"
    outcome = step(image, test_start, code)
    assert outcome.state is not None
    assert not outcome.verified
    assert "without going through `game`" in outcome.problem


def test_writing_memory_behind_games_back_is_caught(image, test_start):
    code = "game.tick(10)\ngame._pyboy.memory[0xC100] = 0x42\ngame.tick(10)"
    outcome = step(image, test_start, code)
    assert not outcome.verified


def test_a_script_error_keeps_the_progress_made(image, test_start):
    outcome = step(image, test_start, "game.tick(30)\nraise RuntimeError('stuck')")
    assert outcome.sandbox.status == "error"
    assert outcome.sandbox.error["message"] == "stuck"
    assert outcome.usable
    assert outcome.frames_used == 30


def test_the_frame_limit_stops_a_script(image, test_start):
    limits = StepLimits(max_frames=100, sandbox=SandboxLimits(timeout_s=20))
    outcome = step(image, test_start, "while True:\n    game.tick(7)", limits=limits)
    assert outcome.sandbox.error["type"] == "FrameLimitExceeded"
    assert outcome.usable
    assert outcome.frames_used == 98


def test_a_timeout_produces_no_state(image, test_start):
    limits = StepLimits(sandbox=SandboxLimits(timeout_s=3))
    outcome = step(image, test_start, "while True:\n    pass", limits=limits)
    assert outcome.state is None
    assert "timeout" in outcome.problem


def test_a_bad_state_is_a_harness_failure(image):
    outcome = step(image, b"not a save state", "game.tick(1)")
    assert outcome.state is None
    assert outcome.problem.startswith("harness failed")


@pytest.mark.parametrize("events, end, why", [
    ("nope", 0, "not a list"),
    ([{"frame": 0, "type": "tick", "frames": 10**9}], 10**9, "limit"),
    ([{"frame": 0, "type": "tick", "frames": -5}], -5, "bad frame count"),
    ([{"frame": 0, "type": "tick", "frames": True}], 1, "bad frame count"),
    ([{"frame": 0, "type": "press", "button": "rm -rf"}], 0, "unknown button"),
    ([{"frame": 0, "type": "poke", "addr": 1}], 0, "unknown type"),
    ([{"frame": 5, "type": "press", "button": "a"}], 0, "out of order"),
    ([{"frame": 0, "type": "press", "button": "a", "extra": 1}], 0, "unexpected fields"),
    ([{"frame": 0, "type": "tick", "frames": 3}], 4, "the step reported"),
])
def test_untrusted_events_are_validated_before_replay(events, end, why):
    assert why in validate_events(events, 0, end, StepLimits(max_frames=1000))


def test_valid_events_pass_validation():
    events = [
        {"frame": 7, "type": "press", "button": "a"},
        {"frame": 7, "type": "tick", "frames": 3},
        {"frame": 10, "type": "release", "button": "a"},
    ]
    assert validate_events(events, 7, 10, StepLimits()) == ""


def test_state_comes_back_intact(image, test_start):
    outcome = step(image, test_start, "pass")
    assert outcome.frames_used == 0
    # No frames: the state is the start state, reloaded and re-saved.
    assert outcome.state == replay(TEST_ROM.read_bytes(), test_start, [])
    assert base64.b64encode(outcome.state)
