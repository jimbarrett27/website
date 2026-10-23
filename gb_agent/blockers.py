"""``report_blocker``: how an agent tells Jim something seems impossible.

Every report is logged in the run. Jim also gets a Telegram message, but not for
every report: repeats of the same problem are merged, and messages are capped and
spaced out per run, so a stuck agent can't spam. The run carries on either way.
"""

import json
import logging
import time
from collections.abc import Callable
from pathlib import Path

logger = logging.getLogger(__name__)


def telegram(message: str) -> None:
    from send_notification import notify  # needs GCP secrets; only when used

    notify(message)


def _key(problem: str) -> str:
    return " ".join(problem.lower().split())[:200]


class BlockerReporter:
    def __init__(self, path: Path, run_id: str, notify: Callable[[str], None] | None = telegram,
                 *, max_messages: int = 5, min_interval_s: float = 600,
                 clock: Callable[[], float] = time.monotonic):
        self.path = Path(path)
        self.run_id = run_id
        self.notify = notify
        self.max_messages = max_messages
        self.min_interval_s = min_interval_s
        self.clock = clock
        self.seen: dict[str, int] = {}
        self.sent = 0
        self.last_sent: float | None = None

    def report(self, problem: str, tried: str, would_help: str, *,
               agent: str, step: int, frame: int) -> str:
        problem, tried, would_help = (str(x).strip()[:1_000] for x in (problem, tried, would_help))
        if not problem:
            return "report_blocker needs a description of the problem."
        key = _key(problem)
        repeat = key in self.seen
        self.seen[key] = self.seen.get(key, 0) + 1

        now = self.clock()
        send = (not repeat and self.notify is not None and self.sent < self.max_messages
                and (self.last_sent is None or now - self.last_sent >= self.min_interval_s))
        delivered = False
        if send:
            try:
                self.notify(f"gb_agent run {self.run_id} — {agent} is blocked (step {step}, "
                            f"frame {frame}):\n{problem}\n\nTried: {tried or '-'}\n"
                            f"Would help: {would_help or '-'}")
                delivered = True
                self.sent += 1
                self.last_sent = now
            except Exception:
                logger.exception("couldn't send a blocker notification")

        with self.path.open("a") as f:
            f.write(json.dumps({
                "agent": agent, "step": step, "frame": frame, "problem": problem,
                "tried": tried, "would_help": would_help, "repeat": repeat,
                "notified": delivered, "time": time.time(),
            }) + "\n")

        if delivered:
            return "Reported to Jim. Carry on with what you can in the meantime."
        if repeat:
            return "Already reported; logged again. Carry on with what you can."
        return "Logged for Jim to read later. Carry on with what you can."
