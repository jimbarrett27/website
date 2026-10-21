"""The tools an agent plays with, as OpenAI-style function schemas plus a dispatcher.

Each tool returns text for the model and, for anything that touches the game,
screenshots. Every argument comes from a model and is checked here; a bad call
gets an error message back, never an exception, so a confused model can recover.
"""

import json
from dataclasses import dataclass, field

from gb_agent.emulator import BUTTONS
from gb_agent.library import ScriptError
from gb_agent.run import Run
from gb_agent.trace import Trace

MAX_TOOL_TEXT = 6_000
REPEAT_NOTE_AT = 3  # identical calls in a row before saying so
TEST_STREAK_NOTE_AT = 4  # test runs in a row before saying so


@dataclass
class ToolResult:
    text: str
    images: list[tuple[str, bytes]] = field(default_factory=list)  # (caption, png)
    trace: Trace | None = None


def _fn(name: str, description: str, properties: dict, required: list[str]) -> dict:
    return {"type": "function", "function": {
        "name": name, "description": description,
        "parameters": {"type": "object", "properties": properties, "required": required},
    }}


_TEST = {"type": "boolean", "description":
         "true: try it and see the result, then throw it away (costs no frames)"}

TOOL_SCHEMAS = [
    _fn("run_script", "Run a script from your library against the game.", {
        "name": {"type": "string"},
        "args": {"type": "object", "description": "keyword arguments for the script"},
        "test": _TEST,
    }, ["name"]),
    _fn("run_code", "Run a one-off Python snippet with `game` in scope "
        "(and `from library.<name> import <name>` available).", {
        "code": {"type": "string"},
        "test": _TEST,
    }, ["code"]),
    _fn("write_script", "Create or replace a script in your library.", {
        "name": {"type": "string", "description": "lowercase_with_underscores"},
        "code": {"type": "string", "description":
                 "Python defining a function with the same name, taking `game` first, "
                 "with a docstring"},
        "reason": {"type": "string", "description": "one line: why this change"},
    }, ["name", "code", "reason"]),
    _fn("read_script", "Show a script's source, now or at an older version.", {
        "name": {"type": "string"},
        "version": {"type": "string"},
    }, ["name"]),
    _fn("list_scripts", "List your library's scripts with how often they're used and fail.",
        {}, []),
    _fn("script_history", "Show every change to a script, newest first.", {
        "name": {"type": "string"},
    }, ["name"]),
    _fn("press", "Press one button: hold it, release, then wait (like game.tap).", {
        "button": {"type": "string", "enum": list(BUTTONS)},
        "hold": {"type": "integer", "description": "frames to hold it, default 8"},
        "after": {"type": "integer", "description": "frames to wait after, default 16"},
    }, ["button"]),
    _fn("wait", "Let the game run without pressing anything.", {
        "frames": {"type": "integer", "description": "60 frames is about one second"},
    }, ["frames"]),
    _fn("screenshot", "See the current screen (doesn't advance the game).", {}, []),
    _fn("read_memory", "Read bytes of game memory (doesn't advance the game).", {
        "addr": {"type": "string", "description": "address, e.g. \"0xC000\""},
        "length": {"type": "integer", "description": "1-64, default 1"},
        "bank": {"type": "integer"},
    }, ["addr"]),
    _fn("watch_memory", "Add (or remove) memory to report before and after every step.", {
        "label": {"type": "string"},
        "addr": {"type": "string", "description": "address, e.g. \"0xC000\""},
        "length": {"type": "integer", "description": "1-64, default 1"},
        "remove": {"type": "boolean"},
    }, ["label"]),
    _fn("report_blocker", "Tell Jim (who set this up) that something seems impossible with "
        "your current tools. He reads these to fix the setup.", {
        "problem": {"type": "string"},
        "tried": {"type": "string"},
        "would_help": {"type": "string"},
    }, ["problem"]),
]

TOOL_NAMES = [schema["function"]["name"] for schema in TOOL_SCHEMAS]


class ToolError(ValueError):
    pass


def _int(args: dict, key: str, default: int | None, lo: int, hi: int) -> int:
    value = args.get(key, default)
    if isinstance(value, str) and value.strip().lstrip("-").isdigit():
        value = int(value)
    if type(value) is not int or not lo <= value <= hi:
        raise ToolError(f"{key} must be a whole number from {lo} to {hi}")
    return value


def _addr(args: dict, key: str = "addr") -> int:
    value = args.get(key)
    try:
        addr = int(value, 0) if isinstance(value, str) else value
    except ValueError:
        addr = None
    if type(addr) is not int or not 0 <= addr <= 0xFFFF:
        raise ToolError(f'{key} must be an address from 0x0000 to 0xFFFF, like "0xC000"')
    return addr


def _str(args: dict, key: str, required: bool = True) -> str:
    value = args.get(key)
    if value is None and not required:
        return ""
    if not isinstance(value, str) or (required and not value.strip()):
        raise ToolError(f"{key} must be a non-empty string")
    return value


def _bool(args: dict, key: str) -> bool:
    value = args.get(key, False)
    if isinstance(value, str):
        return value.strip().lower() == "true"
    return bool(value)


def _trace_result(run: Run, trace: Trace, budget: int) -> ToolResult:
    return ToolResult(f"{trace.to_text(budget)}\n{run.budget_line()}", trace.images, trace)


class Tools:
    """Dispatches tool calls for one agent on one run."""

    def __init__(self, run: Run, agent: str = "main", trace_budget: int = 2_500):
        self.run = run
        self.agent = agent
        self.trace_budget = trace_budget
        self._last_call: str | None = None
        self._repeats = 0
        self._test_streak = 0

    def call(self, name: str, args) -> ToolResult:
        if not isinstance(args, dict):
            return ToolResult(f"Error: arguments for {name} must be a JSON object.")
        method = getattr(self, f"_{name}", None) if name in TOOL_NAMES else None
        if method is None:
            return ToolResult(f"Error: there's no tool called {name!r}. "
                              f"Tools: {', '.join(TOOL_NAMES)}.")
        try:
            result = method(args)
        except (ToolError, ScriptError) as e:
            result = ToolResult(f"Error: {e}")
        if len(result.text) > MAX_TOOL_TEXT:
            result.text = result.text[:MAX_TOOL_TEXT] + "\n…[cut]"
        result.text += self._notes(name, args)
        return result

    def _notes(self, name: str, args: dict) -> str:
        """Plain-spoken nudges when the agent seems stuck in a loop."""
        notes = []
        call = f"{name} {json.dumps(args, sort_keys=True, default=str)}"
        self._repeats = self._repeats + 1 if call == self._last_call else 1
        self._last_call = call
        if self._repeats >= REPEAT_NOTE_AT:
            notes.append(f"You've made this exact call {self._repeats} times in a row. "
                         "If it isn't doing what you want, try something different.")
        if name in ("run_script", "run_code"):
            self._test_streak = self._test_streak + 1 if _bool(args, "test") else 0
            if self._test_streak >= TEST_STREAK_NOTE_AT:
                notes.append(f"That's {self._test_streak} test runs in a row, and test runs "
                             "never change the game. When something works, run it with "
                             "test=false to keep its progress.")
        return "".join(f"\nNote: {note}" for note in notes)

    def _game_step_allowed(self, test: bool) -> None:
        if not test and self.run.frames_left == 0:
            raise ToolError("the frame budget is used up; only test runs are possible")

    # -- game ---------------------------------------------------------------

    def _run_script(self, args: dict) -> ToolResult:
        test = _bool(args, "test")
        self._game_step_allowed(test)
        script_args = args.get("args") or {}
        if isinstance(script_args, str):
            try:
                script_args = json.loads(script_args)
            except json.JSONDecodeError:
                raise ToolError("args must be a JSON object of keyword arguments") from None
        trace = self.run.run_script(_str(args, "name"), script_args, test=test, agent=self.agent)
        return _trace_result(self.run, trace, self.trace_budget)

    def _run_code(self, args: dict) -> ToolResult:
        test = _bool(args, "test")
        self._game_step_allowed(test)
        trace = self.run.run_code(_str(args, "code"), test=test, agent=self.agent)
        return _trace_result(self.run, trace, self.trace_budget)

    def _press(self, args: dict) -> ToolResult:
        self._game_step_allowed(False)
        button = args.get("button")
        if button not in BUTTONS:
            raise ToolError(f"button must be one of {', '.join(BUTTONS)}")
        # hold_frames/wait_frames: the names this tool used before matching game.tap
        args = {"hold": args.get("hold_frames", 8), "after": args.get("wait_frames", 16), **args}
        hold = _int(args, "hold", 8, 1, 600)
        wait = _int(args, "after", 16, 0, 600)
        code = (f"game.press({button!r})\ngame.tick({hold})\ngame.release({button!r})\n"
                + (f"game.tick({wait})\n" if wait else ""))
        trace = self.run.run_code(code, agent=self.agent, title=f"press({button})")
        return _trace_result(self.run, trace, self.trace_budget)

    def _wait(self, args: dict) -> ToolResult:
        self._game_step_allowed(False)
        frames = _int(args, "frames", None, 1, 3_600)
        shortened = frames > self.run.frames_left
        frames = min(frames, self.run.frames_left)
        trace = self.run.run_code(f"game.tick({frames})", agent=self.agent,
                                  title=f"wait({frames})")
        result = _trace_result(self.run, trace, self.trace_budget)
        if shortened:
            result.text = f"(Shortened to the {frames} frames left in the budget.)\n" + result.text
        return result

    def _screenshot(self, args: dict) -> ToolResult:
        return ToolResult(f"The screen at frame {self.run.frame}.",
                          [(f"screen (frame {self.run.frame})", self.run.screenshot_png())])

    def _read_memory(self, args: dict) -> ToolResult:
        addr = _addr(args)
        length = _int(args, "length", 1, 1, 64)
        bank = args.get("bank")
        if bank is not None:
            bank = _int(args, "bank", None, 0, 0x1FF)
        try:
            values = self.run.read_memory(addr, length, bank)
        except ValueError as e:
            raise ToolError(str(e)) from None
        dump = " ".join(f"{v:02x}" for v in values)
        return ToolResult(f"memory at 0x{addr:04X} ({length} bytes): {dump}")

    def _watch_memory(self, args: dict) -> ToolResult:
        label = _str(args, "label")
        if _bool(args, "remove"):
            self.run.watch.pop(label, None)
            return ToolResult(f"Stopped watching {label!r}. Watching: {self._watching()}")
        addr = _addr(args)
        length = _int(args, "length", 1, 1, 64)
        try:
            self.run.set_watch(label, addr, length)
        except ValueError as e:
            raise ToolError(str(e)) from None
        return ToolResult(f"Watching {label!r} at 0x{addr:04X}. Watching: {self._watching()}")

    def _watching(self) -> str:
        return ", ".join(f"{label} (0x{a:04X}, {n})" for label, (a, n, _) in
                         self.run.watch.items()) or "nothing"

    # -- library ------------------------------------------------------------

    def _write_script(self, args: dict) -> ToolResult:
        name = _str(args, "name")
        code = _str(args, "code")
        library = self.run.library
        if library.exists(name) and library.read(name) == code:
            return ToolResult(f"Nothing saved: that's identical to the current {name} "
                              f"(version {library.version(name)}). Change the code to fix it.")
        version = self.run.library.write(name, code, _str(args, "reason"),
                                         agent=self.agent, run=self.run.id, step=self.run.step)
        return ToolResult(f"Saved {name} as version {version}. "
                          f"Run it with run_script(name={name!r}, args={{...}}).")

    def _read_script(self, args: dict) -> ToolResult:
        name = _str(args, "name")
        version = args.get("version") or None
        source = self.run.library.read(name, version)
        current = self.run.library.version(name)
        return ToolResult(f"# {name} @ {version or current}\n{source}")

    def _list_scripts(self, args: dict) -> ToolResult:
        scripts = self.run.library.scripts()
        if not scripts:
            return ToolResult("Your library is empty.")
        usage = self.run.library.usage()
        lines = []
        for info in scripts:
            use = usage.get(info.name, {})
            stats = (f"{use['calls']} runs, {use['failures']} failed"
                     if use else "never run")
            lines.append(f"- {info.signature} @ {info.version}: {info.summary} ({stats})")
        return ToolResult("\n".join(lines))

    def _script_history(self, args: dict) -> ToolResult:
        name = _str(args, "name")
        return ToolResult("\n".join(f"{c.version} {c.date[:16]} {c.reason}"
                                    for c in self.run.library.history(name)))

    # -- people -------------------------------------------------------------

    def _report_blocker(self, args: dict) -> ToolResult:
        return ToolResult(self.run.report_blocker(
            _str(args, "problem"), _str(args, "tried", False),
            _str(args, "would_help", False), self.agent))
