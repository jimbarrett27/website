"""Determinism, the clock lock, and RecordingGame, on the host (no Docker)."""

import time

import pytest

from gb_agent.emulator import (
    EventLimitExceeded,
    FrameLimitExceeded,
    RecordingGame,
    apply_events,
    boot,
    has_rtc,
    save_state,
)


def drive(game: RecordingGame) -> None:
    """A fixed input pattern: menu-ish presses spread over 400 frames."""
    for i in range(10):
        game.tap("start" if i % 3 == 0 else "a", hold=3, after=20)
        game.press("down")
        game.tick(10)
        game.release("down")
    game.tick(400 - game.frames_used)


def record(rom, state, **kwargs) -> tuple[list[dict], bytes]:
    pyboy = boot(rom, state)
    game = RecordingGame(pyboy, **kwargs)
    drive(game)
    return game.events, save_state(pyboy)


def latch_rtc_seconds(pyboy) -> int:
    """Latch the cartridge clock and read its seconds register, the MBC3 way.

    These are cartridge register writes, made directly on a host emulator in a
    test; agent scripts can't do this.
    """
    pyboy.memory[0x0000] = 0x0A  # enable RAM and clock registers
    pyboy.memory[0x6000] = 0x00
    pyboy.memory[0x6000] = 0x01  # latch
    pyboy.memory[0x4000] = 0x08  # select the seconds register
    return pyboy.memory[0xA000]


def test_rom_fixtures_have_clocks(test_rom):
    assert has_rtc(test_rom)


def test_same_state_and_inputs_give_identical_states(test_rom, test_start):
    _, first = record(test_rom, test_start)
    time.sleep(1.2)  # the wall clock moving on must not matter
    _, second = record(test_rom, test_start)
    assert first == second


def test_replaying_recorded_events_reproduces_the_state(test_rom, test_start):
    events, recorded = record(test_rom, test_start)
    pyboy = boot(test_rom, test_start)
    assert apply_events(pyboy, events) == 400
    assert save_state(pyboy) == recorded


def test_steps_chain_on_one_timeline(test_rom, test_start):
    pyboy = boot(test_rom, test_start)
    first = RecordingGame(pyboy)
    first.tap("a")
    middle = save_state(pyboy)

    pyboy = boot(test_rom, middle)
    second = RecordingGame(pyboy, start_frame=first.frame)
    second.tap("b", after=30)
    assert second.events[0]["frame"] == first.frame

    replayed = boot(test_rom, test_start)
    apply_events(replayed, first.events + second.events)
    assert save_state(replayed) == save_state(pyboy)


def test_a_step_ending_with_an_input_still_replays_continuously(test_rom, test_start):
    """PyBoy queues inputs until the next frame and doesn't save the queue."""
    pyboy = boot(test_rom, test_start)
    first = RecordingGame(pyboy)
    first.press("a")
    first.tick(10)
    first.press("start")  # still held, and queued, when the step ends
    first.end_step()
    assert first.events[-3:] == [
        {"frame": 10, "type": "release", "button": "a"},
        {"frame": 10, "type": "release", "button": "start"},
        {"frame": 10, "type": "tick", "frames": 1},
    ]
    assert first.frame == 11 and first.held == set()
    assert {e["button"] for e in first.events if e["type"] == "release"} == {"a", "start"}
    middle = save_state(pyboy)

    pyboy = boot(test_rom, middle)
    second = RecordingGame(pyboy, start_frame=first.frame)
    second.tap("b", after=20)
    second.end_step()

    replayed = boot(test_rom, test_start)
    apply_events(replayed, first.events + second.events)
    assert save_state(replayed) == save_state(pyboy)


def test_end_step_adds_nothing_when_the_step_is_already_clean(test_rom, test_start):
    game = RecordingGame(boot(test_rom, test_start))
    game.tap("a")
    before = list(game.events)
    game.end_step()
    assert game.events == before


def test_clock_is_locked_after_a_state_load(test_rom, test_start):
    pyboy = boot(test_rom, test_start)
    before = latch_rtc_seconds(pyboy)
    time.sleep(1.5)
    assert latch_rtc_seconds(pyboy) == before == 0


def test_silver_is_deterministic_too(silver_rom):
    from gb_agent.emulator import power_on_state

    start = power_on_state(silver_rom)
    _, first = record(silver_rom, start)
    time.sleep(1.2)
    _, second = record(silver_rom, start)
    assert first == second


def test_events_are_logged_with_frames(test_rom, test_start):
    game = RecordingGame(boot(test_rom, test_start), start_frame=100)
    game.press("a")
    game.tick(3)
    game.release("a")
    assert game.events == [
        {"frame": 100, "type": "press", "button": "a"},
        {"frame": 100, "type": "tick", "frames": 3},
        {"frame": 103, "type": "release", "button": "a"},
    ]
    assert game.frame == 103 and game.frames_used == 3
    assert game.held == set()


def test_unknown_buttons_and_bad_frame_counts_are_rejected(test_rom, test_start):
    game = RecordingGame(boot(test_rom, test_start))
    with pytest.raises(ValueError):
        game.press("turbo")
    for bad in (0, -1, 1.5):
        with pytest.raises(ValueError):
            game.tick(bad)
    assert game.events == []


def test_frame_limit(test_rom, test_start):
    game = RecordingGame(boot(test_rom, test_start), max_frames=50)
    game.tick(40)
    with pytest.raises(FrameLimitExceeded):
        game.tick(11)
    assert game.frames_used == 40


def test_event_limit(test_rom, test_start):
    game = RecordingGame(boot(test_rom, test_start), max_events=10)
    with pytest.raises(EventLimitExceeded):
        for _ in range(20):
            game.press("a")
    assert len(game.events) == 10


def test_memory_reads_but_never_writes(test_rom, test_start):
    game = RecordingGame(boot(test_rom, test_start))
    assert isinstance(game.memory[0x0100], int)
    assert len(game.memory[0x0134:0x0143]) == 15  # the cartridge title
    assert isinstance(game.memory[0, 0x0100], int)
    assert game.memory.u16(0x0100) == game.memory[0x0100] | game.memory[0x0101] << 8
    with pytest.raises(TypeError):
        game.memory[0xC000] = 1
    with pytest.raises(TypeError):
        game.memory["0xC000"]


def test_screenshot_and_notes(test_rom, test_start):
    game = RecordingGame(boot(test_rom, test_start))
    game.tick(30)
    assert game.screenshot().size == (160, 144)
    assert game.screenshot_png().startswith(b"\x89PNG")
    game.note("title screen", {"seen": True})
    assert game.notes == [{"frame": 30, "label": "title screen", "value": {"seen": True}}]
