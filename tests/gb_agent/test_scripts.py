"""Library scripts and one-off code, run in the real sandbox."""

import ast
import json

import pytest

from gb_agent.emulator import boot
from gb_agent.games import SILVER
from gb_agent.library import Library, ScriptError
from gb_agent.sandbox import SandboxLimits
from gb_agent.scripts import call_code, run_code, run_script
from gb_agent.steps import StepLimits
from tests.gb_agent.conftest import TEST_ROM, needs_docker

pytestmark = needs_docker

LIMITS = StepLimits(keyframe_every=30, max_keyframes=3, sandbox=SandboxLimits(timeout_s=20))

PRESS_A = '''def press_a(game, times: int = 1) -> int:
    """Tap A `times` times."""
    for _ in range(times):
        game.tap("a", hold=4, after=26)
    return times
'''

MASH = '''from library.press_a import press_a


def mash(game, rounds: int = 2) -> dict:
    """Press A in rounds, using press_a."""
    total = 0
    for i in range(rounds):
        total += press_a(game, times=2)
        game.note("round done", i)
    return {"presses": total}
'''


@pytest.fixture
def library(tmp_path):
    library = Library.create(tmp_path / "library")
    library.write("press_a", PRESS_A, "add press_a")
    library.write("mash", MASH, "add mash")
    return library


def script(image, library, state, name, args=None, **kwargs):
    kwargs.setdefault("limits", LIMITS)
    return run_script(library, name, args, rom_path=TEST_ROM, state=state, image=image, **kwargs)


def test_a_script_runs_and_is_traced(image, library, test_start):
    outcome, trace, version = script(image, library, test_start, "press_a", {"times": 3})
    assert outcome.usable, outcome.problem
    assert outcome.sandbox.value == 3
    assert version == library.version("press_a")
    assert trace.title == f"press_a(times=3) @ {version}"
    assert trace.inputs == "a ×3 (held ~4 frames)"
    captions = [caption for caption, _ in trace.images]
    assert captions[0] == "before (frame 0)" and captions[-1] == "after (frame 90)"
    assert 1 <= len(captions) - 2 <= 3  # keyframes in between
    assert all(png.startswith(b"\x89PNG") for _, png in trace.images)


def test_scripts_import_each_other(image, library, test_start):
    outcome, trace, _ = script(image, library, test_start, "mash", {"rounds": 2})
    assert outcome.usable, outcome.problem
    assert outcome.sandbox.value == {"presses": 4}
    assert [n["label"] for n in trace.notes] == ["round done", "round done"]


def test_usage_is_recorded_against_the_version(image, library, test_start):
    version = library.version("press_a")
    script(image, library, test_start, "press_a")
    library.write("press_a", PRESS_A.replace("hold=4", "hold=5"), "hold longer")
    script(image, library, test_start, "press_a")
    usage = library.usage()["press_a"]
    assert usage["calls"] == 2
    assert usage["versions"][version]["calls"] == 1


def test_a_failing_script_is_counted_as_a_failure(image, library, test_start):
    library.write("broken", 'def broken(game):\n    """Fail."""\n    game.tick(5)\n'
                            '    raise KeyError("missing")\n', "add broken")
    outcome, trace, _ = script(image, library, test_start, "broken")
    assert trace.status == "error"
    assert "KeyError" in trace.to_text()
    assert outcome.usable  # the 5 frames it did advance are still valid
    assert library.usage()["broken"]["failures"] == 1


def test_watched_memory_appears_in_the_trace(image, library, test_start):
    watch = {"wram start": (0xC000, 2, None), "vblank count": (0xFF44, 1, None)}
    _, trace, _ = script(image, library, test_start, "press_a", watch=watch)
    assert [label for label, _, _ in trace.memory] == ["wram start", "vblank count"]
    assert all(len(after) == length for (_, _, after), length in zip(trace.memory, (2, 1)))


def test_bad_watch_lists_are_refused(library, test_start):
    for watch in ({"x": (0x10000, 1, None)}, {"x": (0xC000, 500, None)}, {"x": "C000"},
                  {f"w{i}": (0xC000, 1, None) for i in range(40)}):
        with pytest.raises(ValueError):
            run_script(library, "press_a", {}, rom_path=TEST_ROM, state=test_start, watch=watch)


def test_bad_args_and_unknown_scripts_are_refused(library, test_start):
    for name, args in (("press_a", {"f": object()}), ("press_a", ["a"]), ("nope", {}),
                       ("press_a", {"x": "y" * 5_000})):
        with pytest.raises(ScriptError):
            run_script(library, name, args, rom_path=TEST_ROM, state=test_start)


def test_args_cannot_inject_code():
    args = {"times": "1)); import os; os.system('x') #", "q": "\"'\\\n"}
    tree = ast.parse(call_code("press_a", args))
    assert len(tree.body) == 3  # import json, import the script, call it
    call = tree.body[2].value
    [keywords] = call.keywords  # **json.loads("<a single string constant>")
    [literal] = keywords.value.args
    assert isinstance(literal, ast.Constant) and json.loads(literal.value) == args


def test_one_off_code_can_use_the_library(image, library, test_start):
    code = "from library.press_a import press_a\nresult = press_a(game, times=2) * 10"
    outcome, trace = run_code(library, code, rom_path=TEST_ROM, state=test_start,
                              limits=LIMITS, image=image)
    assert outcome.sandbox.value == 20
    assert trace.title == "one-off code"


def test_the_library_is_read_only_in_the_sandbox(image, library, test_start):
    code = "open('/opt/library/library/press_a.py', 'w').write('hacked')"
    outcome, _ = run_code(library, code, rom_path=TEST_ROM, state=test_start,
                          limits=LIMITS, image=image)
    assert outcome.sandbox.error["type"] in ("OSError", "PermissionError")
    assert "hacked" not in library.read("press_a")


def test_hello_world_goes_out_and_back(image, tmp_path, silver_rom):
    """The seed script, from the bedroom start; position checked on the host only."""
    library = Library.create(tmp_path / "library", SILVER.seed_library)
    start = SILVER.load_start_state()
    outcome, trace, _ = run_script(library, "hello_world", {}, rom_path=SILVER.rom,
                                   state=start, limits=LIMITS, image=image)
    assert outcome.usable, outcome.problem
    assert trace.inputs == "left ×3, right ×3 (held ~8 frames)"
    assert len(trace.notes) == 6
    x = SILVER.progress_values["x"].addr
    assert boot(silver_rom, outcome.state).memory[x] == boot(silver_rom, start).memory[x]
