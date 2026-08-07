"""
Play the game in a window and snapshot named save states as you go.

The states are the test fixtures for the vision agent: play to an interesting
situation, name it, and it lands in pokemon/states/ as a .state next to a .png
of the frame so you can tell them apart later without loading them.

Run it, then type commands in *this terminal* (the game window swallows
keystrokes, so alt-tab back here to save):

    uv run python -m pokemon.state_recorder --rom game_rom.gb
"""

import argparse
import queue
import re
import sys
import threading
from pathlib import Path

from pyboy import PyBoy

DEFAULT_STATES_DIR = Path(__file__).parent / "states"
DEFAULT_ROM = Path("game_rom.gb")

COMMANDS = {"save", "load", "list", "quit", "q", "help"}

# printed on startup and by 'help', and tacked onto --help
USAGE = """commands — type them here, not in the game window:

    blocked          save the current frame as 'blocked'
    save blocked     the same thing, if the name collides with a command
    load blocked     rewind to a state you saved earlier
    list             show what's been captured
    help             print this again
    quit             stop (or just close the window)"""


def slugify(name: str) -> str:
    """
    Turns whatever got typed into a filename-safe stem
    """
    slug = re.sub(r"[^a-z0-9]+", "_", name.strip().lower()).strip("_")
    if not slug:
        raise ValueError(f"'{name}' leaves nothing usable as a filename")
    return slug


def state_paths(states_dir: Path, name: str) -> tuple[Path, Path]:
    """
    The .state and its companion .png for a given name
    """
    slug = slugify(name)
    return states_dir / f"{slug}.state", states_dir / f"{slug}.png"


def save_state(pyboy: PyBoy, states_dir: Path, name: str) -> None:
    state_path, screenshot_path = state_paths(states_dir, name)
    states_dir.mkdir(parents=True, exist_ok=True)

    existed = state_path.exists()
    with state_path.open("wb") as f:
        pyboy.save_state(f)
    pyboy.screen.image.save(screenshot_path)

    print(f"{'overwrote' if existed else 'saved'} {state_path}")


def load_state(pyboy: PyBoy, states_dir: Path, name: str) -> None:
    state_path, _ = state_paths(states_dir, name)
    if not state_path.exists():
        print(f"no state called '{slugify(name)}' in {states_dir}")
        return

    with state_path.open("rb") as f:
        pyboy.load_state(f)
    print(f"loaded {state_path}")


def list_states(states_dir: Path) -> None:
    states = sorted(states_dir.glob("*.state")) if states_dir.exists() else []
    if not states:
        print(f"nothing captured in {states_dir} yet")
        return

    print(f"{len(states)} state(s) in {states_dir}:")
    for state in states:
        print(f"  {state.stem}")


def read_commands(commands: queue.Queue[str]) -> None:
    """
    Feeds stdin lines to the emulator loop, which can't afford to block on input
    """
    for line in sys.stdin:
        commands.put(line.strip())
    commands.put("quit")  # ctrl-D


def handle_command(pyboy: PyBoy, states_dir: Path, command: str) -> bool:
    """
    Runs one typed command. Returns False when it's time to stop.
    """
    verb, _, argument = command.partition(" ")
    verb = verb.lower()

    # a bare name is the common case, so treat anything unrecognised as a save
    if verb not in COMMANDS:
        verb, argument = "save", command

    if verb in {"quit", "q"}:
        return False

    if verb == "help":
        print(USAGE)
    elif verb == "list":
        list_states(states_dir)
    elif not argument.strip():
        print(f"'{verb}' needs a name, e.g. '{verb} blocked'")
    elif verb == "save":
        save_state(pyboy, states_dir, argument)
    elif verb == "load":
        load_state(pyboy, states_dir, argument)

    return True


def record(rom: Path, states_dir: Path, start_from: str | None) -> None:
    pyboy = PyBoy(str(rom))
    pyboy.set_emulation_speed(1)

    try:
        print(f"\nrecording to {states_dir}\n")
        print(USAGE)
        print()
        list_states(states_dir)
        print()

        # after the banner, so the confirmation is the last thing on screen
        if start_from is not None:
            load_state(pyboy, states_dir, start_from)

        commands: queue.Queue[str] = queue.Queue()
        threading.Thread(target=read_commands, args=(commands,), daemon=True).start()

        while pyboy.tick():
            while not commands.empty():
                command = commands.get()
                if not command:
                    continue
                try:
                    if not handle_command(pyboy, states_dir, command):
                        return
                except ValueError as e:
                    print(e)
    finally:
        pyboy.stop()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=f"{__doc__}\n{USAGE}",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--rom", type=Path, default=DEFAULT_ROM, help="path to the game ROM"
    )
    parser.add_argument(
        "--states-dir",
        type=Path,
        default=DEFAULT_STATES_DIR,
        help="where the .state/.png pairs go",
    )
    parser.add_argument(
        "--load",
        dest="start_from",
        help="start from a previously saved state instead of a fresh boot",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.rom.exists():
        sys.exit(f"no ROM at {args.rom} — pass --rom /path/to/rom.gb")

    record(args.rom, args.states_dir, args.start_from)


if __name__ == "__main__":
    main()
