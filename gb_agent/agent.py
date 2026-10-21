"""The agent loop: an LLM calling tools until a limit runs out.

Written directly on LangChain's chat-model interface rather than with
``agents.Agent``, because a small local model needs control over its context:

- **Append-only.** llama-server reuses work for an unchanged prompt prefix, so
  appending a turn costs only the new tokens, while dropping old messages from
  the front forces the whole prompt to be re-read (minutes at 16k on this CPU).
- **Compaction.** Near the context limit the model writes notes for itself, and
  the context restarts from the system prompt, the goal, those notes and the
  current screen. Its scripts survive regardless; they're in the library.
- **Screenshots** come after the tool results as a user message (tool messages
  can't carry images everywhere), and only for the latest step.
"""

import base64
import logging
import time

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, SystemMessage, ToolMessage

from agents.utils import content_to_str
from gb_agent.emulator import BUTTONS
from gb_agent.models import ModelProfile
from gb_agent.run import Run
from gb_agent.tools import TOOL_SCHEMAS, Tools

logger = logging.getLogger(__name__)

COMPACT_AT = 0.75  # of the context window
MAX_IDLE_TURNS = 3  # replies without a tool call, in a row, before the run ends
LLM_RETRIES = 3

SYSTEM_PROMPT = """\
You are playing a Game Boy game through tools. Nobody is watching live; keep going \
on your own until the run's budget runs out.

The idea is to build up a library of scripts: Python functions that do multi-step \
things for you (walk somewhere, get through a menu, mash through text), so you can \
decide *what* to do while your scripts handle *how*. You can also press buttons \
directly, which is fine for exploring.

Scripts and snippets run in a sandbox with `game`, which has:
  game.press(button) / game.release(button)   buttons: {buttons}
  game.tick(frames=1)      advance time; 60 frames is about one second
  game.tap(button, hold=2, after=6)   press, hold, release, wait
  game.frame               frames since the run started
  game.memory[addr]        read a byte (memory[a:b] for a list); memory is read-only
  game.screenshot()        the screen as a PIL image (160x144)
  game.note(label, value)  record an observation; it shows up in your report
A script is one file defining one function with the same name, taking `game` first, \
with a docstring, for example:
  def walk_left(game, tiles: int = 1) -> int:
      \"\"\"Walk left `tiles` tiles.\"\"\"
      ...
Scripts can use each other: `from library.walk_left import walk_left`.

After each step you get a report (what happened, inputs used, notes, errors) and \
screenshots. Use test=true on run_script or run_code to try something and throw the \
result away: it costs no frames. Kept steps spend the frame budget.

Your context is limited. When it fills up you'll be asked to write notes for \
yourself, and everything else you've seen will be forgotten, except your scripts. \
If something seems impossible with the tools you have, use report_blocker.

Every reply should call a tool. If you want to think, write it briefly in the same \
reply as the tool call.

The game: {notes}"""

COMPACT_PROMPT = """\
Your context is nearly full and is about to be cleared. Write notes for yourself: \
what you've learned about the game and its controls, where you are and what you're \
doing, which scripts work and which don't, and what to do next. Be specific and \
brief (at most about 300 words). Reply with the notes only."""


def _image_part(png: bytes) -> dict:
    return {"type": "image_url",
            "image_url": {"url": "data:image/png;base64," + base64.b64encode(png).decode()}}


def _upscale(png: bytes, factor: int = 2) -> bytes:
    """Game Boy screens are tiny; doubling them helps vision models read text."""
    import io

    from PIL import Image

    image = Image.open(io.BytesIO(png))
    image = image.resize((image.width * factor, image.height * factor), Image.NEAREST)
    out = io.BytesIO()
    image.save(out, format="PNG")
    return out.getvalue()


def _estimate_tokens(messages: list[AnyMessage]) -> int:
    total = 0
    for message in messages:
        content = message.content
        if isinstance(content, str):
            total += len(content) // 3
        else:
            for part in content:
                total += 300 if part.get("type") == "image_url" else len(part.get("text", "")) // 3
        total += sum(len(str(call)) // 3 for call in getattr(message, "tool_calls", []) or [])
    return total


class GameAgent:
    def __init__(self, run: Run, llm: BaseChatModel, profile: ModelProfile, *,
                 name: str = "main", describer: BaseChatModel | None = None):
        self.run = run
        self.profile = profile
        self.name = name
        self.base_llm = llm
        self.llm = llm.bind_tools(TOOL_SCHEMAS)
        # Same tools in the prompt, so the server can reuse the cached prefix (the
        # tool definitions are part of it), but the model must answer in text.
        self.notes_llm = llm.bind_tools(TOOL_SCHEMAS, tool_choice="none")
        self.describer = describer
        self.tools = Tools(run, agent=name)
        self.system = SystemMessage(SYSTEM_PROMPT.format(
            buttons=", ".join(BUTTONS),
            notes=run.game.notes or "(no notes)"))
        self.messages: list[AnyMessage] = []
        self.context_tokens = 0  # as of the last call
        self.compactions = 0

    # -- messages -----------------------------------------------------------

    def _opening(self, notes: str | None = None) -> list[AnyMessage]:
        c = self.run.config
        text = (f"Your goal: {c.goal}\n\nBudget: {c.frame_budget} frames "
                f"(about {c.frame_budget // 60} seconds of game time), {c.max_llm_calls} LLM "
                f"calls. {self.run.budget_line()}\n\nYour library has: "
                + (", ".join(i.name for i in self.run.library.scripts()) or "nothing yet")
                + ". Use list_scripts and read_script to look at them.")
        if notes:
            text += f"\n\nYour notes from earlier in this run:\n{notes}"
        return [self.system, self._with_screens(text, [
            (f"the screen now (frame {self.run.frame})", self.run.screenshot_png())])]

    def _with_screens(self, text: str, images: list[tuple[str, bytes]]) -> HumanMessage:
        images = images[-self.profile.images_per_step:] if self.profile.images_per_step else []
        if not images:
            return HumanMessage(text)
        if not self.profile.vision:
            return HumanMessage(text + "\n\n" + "\n".join(
                f"[{caption}] {self._describe(png)}" for caption, png in images))
        parts: list[dict] = [{"type": "text", "text": text + "\n\nScreenshots: "
                              + ", ".join(caption for caption, _ in images)}]
        parts += [_image_part(_upscale(png)) for _, png in images]
        return HumanMessage(parts)

    def _describe(self, png: bytes) -> str:
        if self.describer is None:
            return "(no description available: this model can't see images)"
        reply = self._invoke(self.describer, [HumanMessage([
            {"type": "text", "text": "Describe this Game Boy screen in two or three "
             "sentences: what's shown, any text, and where the player is."},
            _image_part(_upscale(png))])], purpose="describe")
        return content_to_str(reply.content).strip()

    # -- the loop -----------------------------------------------------------

    def play(self) -> str:
        self.messages = self._opening()
        idle = 0
        while (reason := self.run.limit_reached()) is None:
            if self.context_tokens > self.profile.context_window * COMPACT_AT:
                self._compact()
            try:
                response = self._invoke(self.llm, self.messages, purpose="act")
            except Exception as e:
                logger.exception("LLM call failed")
                return f"llm_error: {e}"
            self.messages.append(response)

            calls = list(response.tool_calls or [])
            bad = list(getattr(response, "invalid_tool_calls", None) or [])
            if not calls and not bad:
                idle += 1
                if idle >= MAX_IDLE_TURNS:
                    return "agent_stopped"
                self.messages.append(HumanMessage(
                    f"Keep playing: call a tool. {self.run.budget_line()}"))
                continue
            idle = 0

            images: list[tuple[str, bytes]] = []
            for call in calls:
                result = self.tools.call(call["name"], call.get("args"))
                self.messages.append(ToolMessage(result.text, tool_call_id=call["id"],
                                                 name=call["name"]))
                images += result.images
                self.run.log_agent({"agent": self.name, "kind": "tool", "tool": call["name"],
                                    "args": call.get("args"), "result": result.text,
                                    "step": self.run.step})
            for call in bad:
                text = (f"Error: couldn't read that tool call ({call.get('error') or 'bad JSON'}). "
                        "Arguments must be valid JSON.")
                self.messages.append(ToolMessage(text, tool_call_id=call.get("id") or "invalid",
                                                 name=call.get("name") or "unknown"))
            if images:
                self.messages.append(self._with_screens(
                    "Screenshots from that step are below. Call your next tool.", images))
        return reason

    def _invoke(self, llm, messages: list[AnyMessage], *, purpose: str) -> AIMessage:
        for attempt in range(LLM_RETRIES):
            started = time.monotonic()
            try:
                response = llm.invoke(messages)
                break
            except Exception:
                if attempt == LLM_RETRIES - 1:
                    raise
                logger.warning("LLM call failed (attempt %d), retrying", attempt + 1,
                               exc_info=True)
                time.sleep(5 * 2 ** attempt)
        usage = response.usage_metadata or {}
        input_tokens = usage.get("input_tokens") or _estimate_tokens(messages)
        output_tokens = usage.get("output_tokens") or len(content_to_str(response.content)) // 3
        self.run.llm_calls += 1
        self.run.tokens += input_tokens + output_tokens
        if purpose == "act":
            self.context_tokens = input_tokens + output_tokens
        self.run.log_agent({
            "agent": self.name, "kind": "llm", "purpose": purpose,
            "seconds": round(time.monotonic() - started, 1),
            "input_tokens": input_tokens, "output_tokens": output_tokens,
            "text": content_to_str(response.content),
            "reasoning": (response.additional_kwargs or {}).get("reasoning_content"),
            "tool_calls": [{"name": c["name"], "args": c.get("args")}
                           for c in response.tool_calls or []],
            "invalid_tool_calls": [dict(c) for c in getattr(response, "invalid_tool_calls", [])],
            "llm_calls": self.run.llm_calls, "step": self.run.step,
        })
        return response

    def _compact(self) -> None:
        # Appended to the existing context, so only the request itself is new input.
        request = self.messages + [HumanMessage(COMPACT_PROMPT)]
        try:
            notes = content_to_str(self._invoke(self.notes_llm, request,
                                                purpose="compact").content).strip()
        except Exception:
            logger.exception("compaction failed; continuing without notes")
            notes = ""
        if not notes:
            notes = "(writing notes failed; start again from the screen and your scripts)"
        self.compactions += 1
        self.run.log_agent({"agent": self.name, "kind": "compaction", "notes": notes,
                            "compactions": self.compactions, "step": self.run.step})
        self.messages = self._opening(notes)
        self.context_tokens = _estimate_tokens(self.messages)
