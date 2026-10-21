"""Sub-agents: helpers the main agent designs and hands one job to.

The main agent writes a spec (instructions, a subset of its own tools, which
library scripts it may run, which model) with ``define_subagent``; the spec is
saved in the run's library and versioned like a script. ``run_subagent`` starts
it on a task with a fresh context, and only its closing summary (plus a few
numbers and the final screen) goes back into the main agent's context. That's
the point: long, fiddly jobs don't eat the main agent's small context.

Limits:
- a sub-agent only gets tools its parent has, and never the sub-agent tools
  themselves, so nesting stops at one level;
- each run has its own LLM-call and frame allowance, inside the run's limits;
- it uses the same sandboxed tools, so it can't reach anything the main agent
  can't.
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass

from langchain_core.language_models import BaseChatModel

from gb_agent.library import ScriptError, check_name
from gb_agent.models import PROFILES, ModelProfile, get_profile
from gb_agent.run import Run

logger = logging.getLogger(__name__)

SUBAGENT_TOOLS = ("define_subagent", "run_subagent", "list_subagents")
MAX_PROMPT_CHARS = 4_000
DEFAULT_CALLS, MAX_CALLS = 15, 50
DEFAULT_FRAMES = 3_000
MAX_SUMMARY_CHARS = 2_000


@dataclass(frozen=True)
class SubAgentSpec:
    name: str
    purpose: str  # one line, shown in listings
    instructions: str  # the sub-agent's own instructions, written by the parent
    tools: tuple[str, ...]  # a subset of the parent's tools
    scripts: tuple[str, ...]  # library scripts it may run; empty means any
    model: str  # a model profile name

    def to_json(self) -> dict:
        return {"name": self.name, "purpose": self.purpose, "instructions": self.instructions,
                "tools": list(self.tools), "scripts": list(self.scripts), "model": self.model}

    @classmethod
    def from_json(cls, data: dict) -> "SubAgentSpec":
        return cls(data["name"], data["purpose"], data["instructions"], tuple(data["tools"]),
                   tuple(data["scripts"]), data["model"])


def allowed_models(parent: ModelProfile, allow_paid: bool) -> list[str]:
    """The parent's own model, plus paid models if the run allows them.

    Other local profiles are out: the local server runs one model at a time.
    """
    return [parent.name] + [p.name for p in PROFILES.values()
                            if allow_paid and p.paid and p.name != parent.name]


def check_spec(raw: dict, *, parent_tools: list[str], parent_model: ModelProfile,
               allow_paid: bool) -> SubAgentSpec:
    """A validated spec from a model's tool arguments, or a ScriptError saying why not."""
    name = check_name(raw.get("name"))
    purpose = " ".join(str(raw.get("purpose") or "").split())
    if not purpose or len(purpose) > 200:
        raise ScriptError("purpose must be one line of at most 200 characters")
    instructions = str(raw.get("instructions") or "").strip()
    if not instructions or len(instructions) > MAX_PROMPT_CHARS:
        raise ScriptError(f"instructions must be 1-{MAX_PROMPT_CHARS} characters")

    tools = raw.get("tools")
    if not isinstance(tools, list) or not tools or not all(isinstance(t, str) for t in tools):
        raise ScriptError("tools must be a non-empty list of tool names")
    grantable = [t for t in parent_tools if t not in SUBAGENT_TOOLS]
    if bad := [t for t in tools if t not in grantable]:
        raise ScriptError(f"can't give a sub-agent {', '.join(bad)}; it can have any of: "
                          f"{', '.join(grantable)}")

    scripts = raw.get("scripts") or []
    if not isinstance(scripts, list) or not all(isinstance(s, str) for s in scripts):
        raise ScriptError("scripts must be a list of script names")
    for script in scripts:
        check_name(script)
    if scripts and "run_script" not in tools:
        raise ScriptError("listing scripts only makes sense with the run_script tool")

    model = raw.get("model") or parent_model.name
    allowed = allowed_models(parent_model, allow_paid)
    if model not in allowed:
        raise ScriptError(f"model must be one of: {', '.join(allowed)}")
    return SubAgentSpec(name, purpose, instructions, tuple(dict.fromkeys(tools)),
                        tuple(dict.fromkeys(scripts)), model)


@dataclass
class SubAgentResult:
    name: str
    version: str
    agent: str  # e.g. "walker#2", as tagged in the run's logs and events
    reason: str  # "finished", "max_calls", or a run limit
    summary: str
    calls: int
    frames: int
    kept_steps: int
    screen_png: bytes


class SubAgentHost:
    """What the main agent's tools need to define and run sub-agents."""

    def __init__(self, run: Run, parent_profile: ModelProfile,
                 model_factory: Callable[[ModelProfile], BaseChatModel], *,
                 allow_paid: bool = False, describer: BaseChatModel | None = None):
        self.run = run
        self.parent_profile = parent_profile
        self.model_factory = model_factory
        self.allow_paid = allow_paid
        self.describer = describer
        self.runs = 0
        self._models: dict[str, BaseChatModel] = {}

    def run_subagent(self, name: str, task: str, *, max_calls: int, max_frames: int,
                     parent: str) -> SubAgentResult:
        from gb_agent.agent import GameAgent  # the agent module imports the tools module
        from gb_agent.tools import Tools

        spec = SubAgentSpec.from_json(self.run.library.read_subagent(name))
        version = self.run.library.subagent_version(name)
        profile = get_profile(spec.model)
        if spec.model not in allowed_models(self.parent_profile, self.allow_paid):
            raise ScriptError(f"{name} uses {spec.model}, which this run can't use")
        if spec.model not in self._models:
            self._models[spec.model] = self.model_factory(profile)

        self.runs += 1
        agent_name = f"{name}#{self.runs}"
        tools = Tools(self.run, agent=agent_name, allowed=(*spec.tools, "finish"),
                      scripts=spec.scripts or None, frame_allowance=max_frames)
        agent = GameAgent(self.run, self._models[spec.model], profile, name=agent_name,
                          tools=tools, instructions=spec.instructions, task=task,
                          max_calls=max_calls, describer=self.describer)
        frame, kept, calls = self.run.frame, self.run.kept_steps, self.run.llm_calls
        self.run.log_agent({"agent": parent, "kind": "subagent_start", "subagent": agent_name,
                            "version": version, "task": task, "max_calls": max_calls,
                            "max_frames": max_frames, "step": self.run.step})
        reason = agent.play()
        summary = (tools.finished or "").strip()[:MAX_SUMMARY_CHARS]
        result = SubAgentResult(
            name=name, version=version, agent=agent_name, reason=reason,
            summary=summary or "(it ended without calling finish, so there's no summary)",
            calls=self.run.llm_calls - calls, frames=self.run.frame - frame,
            kept_steps=self.run.kept_steps - kept, screen_png=self.run.screenshot_png())
        self.run.library.record_use(name, version, ok=reason == "finished",
                                    frames=result.frames, kind="subagent",
                                    error=None if reason == "finished" else reason)
        self.run.log_agent({"agent": parent, "kind": "subagent_end", "subagent": agent_name,
                            "reason": reason, "summary": summary, "calls": result.calls,
                            "frames": result.frames, "step": self.run.step})
        return result
