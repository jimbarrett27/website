"""report_blocker: logged every time, sent to Jim sparingly (no Docker)."""

import json

from gb_agent.blockers import BlockerReporter
from gb_agent.play import main as play_main


class Clock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


def reporter(tmp_path, sent, clock, **kwargs):
    return BlockerReporter(tmp_path / "blockers.jsonl", "run-1", notify=sent.append,
                           clock=clock, **kwargs)


def report(r, problem):
    return r.report(problem, "tried things", "a tool", agent="main", step=3, frame=99)


def test_first_report_is_sent_and_logged(tmp_path):
    sent, clock = [], Clock()
    r = reporter(tmp_path, sent, clock)
    assert report(r, "Can't open the menu").startswith("Reported to Jim")
    assert len(sent) == 1 and "Can't open the menu" in sent[0] and "run-1" in sent[0]
    [entry] = [json.loads(line) for line in (tmp_path / "blockers.jsonl").read_text().splitlines()]
    assert entry["notified"] and entry["step"] == 3 and entry["frame"] == 99


def test_repeats_are_merged(tmp_path):
    sent, clock = [], Clock()
    r = reporter(tmp_path, sent, clock, min_interval_s=0)
    report(r, "Can't open the menu")
    assert report(r, "can't  OPEN the menu").startswith("Already reported")
    assert len(sent) == 1
    assert len((tmp_path / "blockers.jsonl").read_text().splitlines()) == 2


def test_messages_are_spaced_out_and_capped(tmp_path):
    sent, clock = [], Clock()
    r = reporter(tmp_path, sent, clock, max_messages=2, min_interval_s=600)
    report(r, "one")
    clock.now = 100
    assert report(r, "two").startswith("Logged for Jim")  # too soon
    clock.now = 700
    report(r, "three")
    clock.now = 2_000
    report(r, "four")  # over the cap
    assert [m.split("\n")[1] for m in sent] == ["one", "three"]


def test_a_failing_notifier_doesnt_break_the_run(tmp_path):
    def broken(message):
        raise ConnectionError("no network")

    r = BlockerReporter(tmp_path / "b.jsonl", "run-1", notify=broken)
    assert report(r, "stuck").startswith("Logged")


def test_without_notifications_everything_is_still_logged(tmp_path):
    r = BlockerReporter(tmp_path / "b.jsonl", "run-1", notify=None)
    report(r, "stuck")
    assert json.loads((tmp_path / "b.jsonl").read_text())["notified"] is False


def test_paid_models_need_explicit_permission(capsys):
    assert play_main(["--model", "claude-haiku-5.5"]) == 2
    assert "--allow-paid" in capsys.readouterr().err
