"""The script library: validation, versions, history and usage (no Docker)."""

import subprocess

import pytest

from gb_agent.games import SILVER
from gb_agent.library import Library, ScriptError, check_script

GOOD = '''def wait(game, frames: int = 10) -> int:
    """Wait a while."""
    game.tick(frames)
    return game.frame
'''


@pytest.fixture
def library(tmp_path):
    return Library.create(tmp_path / "library", SILVER.seed_library, run="run-1")


def git_log(library, *args):
    return subprocess.run(["git", "-C", str(library.root), "log", *args],
                          capture_output=True, text=True, check=True).stdout


def test_created_with_the_seed_scripts(library):
    [info] = library.scripts()
    assert info.name == "hello_world"
    assert info.signature == "hello_world(game, taps: int=3)"
    assert info.summary.startswith("Tap left")
    assert "Seed the library" in git_log(library, "--format=%B")
    assert "Run: run-1" in git_log(library, "--format=%B")


def test_writing_makes_a_version_with_the_reason(library):
    version = library.write("wait", GOOD, "Add a script that waits",
                            agent="main", run="run-1", step=4)
    assert library.version("wait") == version
    message = git_log(library, "-1", "--format=%B")
    assert message.startswith("Add a script that waits")
    assert "Agent: main" in message and "Step: 4" in message


def test_old_versions_are_kept(library):
    first = library.write("wait", GOOD, "first")
    second = library.write("wait", GOOD.replace("10", "20"), "wait longer")
    assert first != second
    assert "frames: int = 10" in library.read("wait", first)
    assert "frames: int = 20" in library.read("wait")
    assert [c.reason for c in library.history("wait")] == ["wait longer", "first"]
    assert [c.version for c in library.history("wait")] == [second, first]


def test_an_unchanged_script_keeps_its_version(library):
    first = library.write("wait", GOOD, "first")
    commits = git_log(library, "--format=%h").split()
    assert library.write("wait", GOOD, "again") == first
    assert git_log(library, "--format=%h").split() == commits


def test_versions_are_per_script(library):
    hello = library.version("hello_world")
    library.write("wait", GOOD, "add wait")
    assert library.version("hello_world") == hello


@pytest.mark.parametrize("name, code, why", [
    ("Wait", GOOD, "bad script name"),
    ("../evil", GOOD, "bad script name"),
    ("class", GOOD, "bad script name"),
    ("_private", GOOD, "bad script name"),
    ("wait", "def wait(game:\n", "syntax error"),
    ("wait", "def other(game):\n    'doc'\n", "must define a top-level function wait"),
    ("wait", "def wait(frames):\n    'doc'\n", "first parameter must be `game`"),
    ("wait", "def wait():\n    'doc'\n", "first parameter must be `game`"),
    ("wait", "def wait(game):\n    pass\n", "needs a docstring"),
    ("wait", "x = '" + "y" * 70_000 + "'", "at most"),
])
def test_bad_scripts_are_rejected(library, name, code, why):
    with pytest.raises(ScriptError, match=why):
        library.write(name, code, "try")


def test_a_reason_is_required(library):
    with pytest.raises(ScriptError, match="reason"):
        library.write("wait", GOOD, "   ")


def test_bad_versions_and_missing_scripts(library):
    with pytest.raises(ScriptError):
        library.read("hello_world", "--output=/tmp/x")
    with pytest.raises(ScriptError):
        library.read("hello_world", "deadbeef")
    with pytest.raises(ScriptError):
        library.read("nope")
    with pytest.raises(ScriptError):
        library.version("nope")


def test_files_are_readable_by_the_sandbox_user(library):
    library.write("wait", GOOD, "add")
    assert library.package_dir.stat().st_mode & 0o755 == 0o755
    assert library.path("wait").stat().st_mode & 0o644 == 0o644


def test_git_hooks_never_run(tmp_path):
    library = Library.create(tmp_path / "lib")
    hook = library.root / ".git" / "hooks" / "pre-commit"
    hook.write_text(f"#!/bin/sh\ntouch {tmp_path}/hook-ran\n")
    hook.chmod(0o755)
    library.write("wait", GOOD, "add")
    assert not (tmp_path / "hook-ran").exists()


def test_usage_is_counted_per_version(library):
    v1 = library.write("wait", GOOD, "first")
    library.record_use("wait", v1, ok=True, frames=10)
    library.record_use("wait", v1, ok=False, frames=4, error="ValueError")
    v2 = library.write("wait", GOOD.replace("10", "20"), "second")
    library.record_use("wait", v2, ok=True, frames=20)
    usage = library.usage()["wait"]
    assert (usage["calls"], usage["failures"], usage["frames"]) == (3, 1, 34)
    assert usage["versions"][v1] == {"calls": 2, "failures": 1, "frames": 14}
    assert usage["versions"][v2] == {"calls": 1, "failures": 0, "frames": 20}


def test_seed_scripts_are_valid():
    for path in SILVER.seed_library.glob("*.py"):
        check_script(path.stem, path.read_text())


def test_create_refuses_a_non_empty_directory(tmp_path):
    (tmp_path / "lib").mkdir()
    (tmp_path / "lib" / "something").write_text("x")
    with pytest.raises(FileExistsError):
        Library.create(tmp_path / "lib")
