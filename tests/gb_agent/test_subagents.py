"""Sub-agents: specs, validation, and running them, with scripted fake models."""

import json

import pytest

from gb_agent.agent import GameAgent
from gb_agent.library import ScriptError
from gb_agent.models import get_profile
from gb_agent.subagents import SubAgentHost, allowed_models, check_spec
from gb_agent.tools import TOOL_NAMES, Tools
from tests.gb_agent.conftest import needs_docker
from tests.gb_agent.test_agent import ScriptedModel, call, game, make_run, say  # noqa: F401

LOCAL = get_profile("qwen3-vl-2b-local")
PARENT_TOOLS = [*TOOL_NAMES, "define_subagent", "run_subagent", "list_subagents"]
assert "update_notes" in TOOL_NAMES

SPEC = {"name": "walker", "purpose": "walk places", "instructions": "Use walk. Stop when done.",
        "tools": ["run_script", "wait"], "scripts": ["walk"], "reason": "need a walker"}


def check(**changes):
    return check_spec({**SPEC, **changes}, parent_tools=PARENT_TOOLS, parent_model=LOCAL,
                      allow_paid=False)


# -- validation (no Docker) --------------------------------------------------

def test_a_valid_spec():
    spec = check(tools=["run_script", "wait", "run_script"])
    assert spec.tools == ("run_script", "wait") and spec.model == LOCAL.name


@pytest.mark.parametrize("changes, why", [
    ({"name": "Bad Name"}, "bad script name"),
    ({"purpose": ""}, "purpose"),
    ({"instructions": "x" * 5_000}, "instructions"),
    ({"tools": []}, "non-empty list"),
    ({"tools": ["teleport"]}, "can't give a sub-agent teleport"),
    ({"tools": ["run_subagent"]}, "can't give a sub-agent run_subagent"),
    ({"tools": ["define_subagent", "wait"]}, "can't give a sub-agent define_subagent"),
    ({"tools": ["update_notes"]}, "can't give a sub-agent update_notes"),
    ({"tools": ["wait"], "scripts": ["walk"]}, "only makes sense with the run_script tool"),
    ({"scripts": ["../x"]}, "bad script name"),
    ({"model": "qwen3-vl-8b-local"}, "model must be one of"),
    ({"model": "claude-haiku-5.5"}, "model must be one of"),
])
def test_bad_specs_are_refused(changes, why):
    with pytest.raises(ScriptError, match=why):
        check(**changes)


def test_paid_models_only_when_the_run_allows_them():
    assert allowed_models(LOCAL, allow_paid=False) == [LOCAL.name]
    assert "claude-haiku-5.5" in allowed_models(LOCAL, allow_paid=True)
    spec = check_spec({**SPEC, "model": "claude-haiku-5.5"}, parent_tools=PARENT_TOOLS,
                      parent_model=LOCAL, allow_paid=True)
    assert spec.model == "claude-haiku-5.5"


# -- in a run (Docker) ---------------------------------------------------------

def host_for(run, sub_model):
    return SubAgentHost(run, LOCAL, lambda profile: sub_model)


def jsonl(run, name):
    path = run.dir / name
    return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []


@needs_docker[0]
@needs_docker[1]
def test_main_agent_tools_depend_on_having_a_host(make_run):
    run = make_run()
    assert "run_subagent" not in Tools(run).allowed
    assert {"define_subagent", "run_subagent", "list_subagents"} <= set(
        Tools(run, host=host_for(run, None)).allowed)


@needs_docker[0]
@needs_docker[1]
def test_specs_are_saved_and_versioned(make_run):
    run = make_run()
    tools = Tools(run, host=host_for(run, None))
    assert "Saved sub-agent walker" in tools.call("define_subagent", SPEC).text
    first = run.library.subagent_version("walker")
    assert tools.call("define_subagent", SPEC).text.startswith("Nothing saved")
    tools.call("define_subagent", {**SPEC, "purpose": "walk further", "reason": "clearer"})
    assert run.library.subagent_version("walker") != first
    assert run.library.read_subagent("walker", first)["purpose"] == "walk places"
    assert [c.reason for c in run.library.subagent_history("walker")] == [
        "clearer", "need a walker"]
    listing = tools.call("list_subagents", {}).text
    assert "walker @" in listing and "walk further" in listing and "never run" in listing
    assert "Error" in tools.call("define_subagent", {**SPEC, "tools": ["run_subagent"]}).text


@needs_docker[0]
@needs_docker[1]
def test_a_sub_agent_does_a_job_and_reports_back(make_run):
    run = make_run()
    sub = ScriptedModel(replies=[
        say(call("run_script", name="walk", args={"frames": 40})),
        say(call("finish", summary="Walked right for 40 frames; the screen scrolled.")),
    ])
    main = ScriptedModel(replies=[
        say(call("define_subagent", **SPEC)),
        say(call("run_subagent", name="walker", task="Walk right a bit.", max_calls=5,
                 max_frames=200)),
        say(text="done"), say(text="done"), say(text="done"),
    ])
    agent = GameAgent(run, main, LOCAL, host=host_for(run, sub))
    agent.play()

    report = [m.content for m in main.seen[2] if getattr(m, "type", "") == "tool"][-1]
    assert "Sub-agent walker#1" in report and "ended: finished" in report
    assert "Walked right for 40 frames" in report
    assert "It used 2 LLM calls and 41 frames" in report  # 40, then end_step's frame

    # the sub-agent saw only its own job and tools
    assert "Your job: Walk right a bit." in sub.seen[0][1].content[0]["text"]
    assert "Use walk. Stop when done." in sub.seen[0][0].content

    events = jsonl(run, "events.jsonl")
    assert {e["agent"] for e in events} == {"walker#1"}
    assert run.frame == 41 and run.final_state_replays()
    kinds = [r["kind"] for r in jsonl(run, "agents.jsonl")]
    assert "subagent_start" in kinds and "subagent_end" in kinds
    assert run.library.usage(kind="subagent")["walker"]["calls"] == 1
    assert "walk" in run.library.usage()  # script usage is still counted


@needs_docker[0]
@needs_docker[1]
def test_a_sub_agent_cannot_nest_or_go_beyond_its_scripts(make_run):
    run = make_run()
    run.library.write("other", 'def other(game):\n    """Other."""\n    game.tick(5)\n', "add")
    sub = ScriptedModel(replies=[
        say(call("run_subagent", name="walker", task="recurse")),
        say(call("run_script", name="other")),
        say(call("finish", summary="couldn't")),
    ])
    tools = Tools(run, host=host_for(run, sub))
    tools.call("define_subagent", SPEC)
    text = tools.call("run_subagent", {"name": "walker", "task": "try things"}).text
    assert "ended: finished" in text
    seen = [m.content for m in sub.seen[-1] if getattr(m, "type", "") == "tool"]
    assert "you don't have a tool called 'run_subagent'" in seen[0]
    assert "you may only run these scripts: walk" in seen[1]
    assert run.frame == 0


@needs_docker[0]
@needs_docker[1]
def test_a_sub_agent_is_held_to_its_frame_allowance(make_run):
    run = make_run()
    sub = ScriptedModel(replies=[
        say(call("wait", frames=500)),
        say(call("wait", frames=10)),
    ])
    tools = Tools(run, host=host_for(run, sub))
    tools.call("define_subagent", SPEC)
    text = tools.call("run_subagent", {"name": "walker", "task": "wait", "max_frames": 60}).text
    assert "ended: max_frames" in text
    assert run.frame == 60
    assert len(sub.seen) == 1  # the allowance was gone, so no second call
    [waited] = [r for r in jsonl(run, "agents.jsonl") if r.get("tool") == "wait"]
    assert waited["agent"] == "walker#1" and "Shortened to 60 frames" in waited["result"]


@needs_docker[0]
@needs_docker[1]
def test_a_sub_agent_that_never_finishes_runs_out_of_calls(make_run):
    run = make_run()
    sub = ScriptedModel(replies=[say(call("screenshot"))] * 10)
    tools = Tools(run, host=host_for(run, sub))
    tools.call("define_subagent", SPEC)
    text = tools.call("run_subagent", {"name": "walker", "task": "look", "max_calls": 3}).text
    assert "ended: max_calls" in text and "It used 3 LLM calls" in text
    assert "ended without calling finish" in text
    usage = run.library.usage(kind="subagent")["walker"]
    assert usage["failures"] == 1


@needs_docker[0]
@needs_docker[1]
def test_the_opening_suggests_sub_agents_only_when_available(make_run):
    run = make_run()
    with_host = GameAgent(run, ScriptedModel(), LOCAL, host=host_for(run, None))
    without = GameAgent(run, ScriptedModel(), LOCAL)
    assert "consider a sub-agent" in with_host._opening()[1].content[0]["text"]
    assert "consider a sub-agent" not in without._opening()[1].content[0]["text"]
    run.notes = "already under way"
    assert "consider a sub-agent" not in with_host._opening()[1].content[0]["text"]


@needs_docker[0]
@needs_docker[1]
def test_unknown_sub_agents_and_bad_limits_are_errors(make_run):
    run = make_run()
    tools = Tools(run, host=host_for(run, None))
    assert tools.call("run_subagent", {"name": "nobody", "task": "x"}).text.startswith("Error")
    tools.call("define_subagent", SPEC)
    assert "max_calls" in tools.call("run_subagent", {"name": "walker", "task": "x",
                                                      "max_calls": 500}).text
