"""Runs one untrusted snippet and reports what happened.

This file is the sandbox container's entrypoint. It reads a JSON request on stdin:

    {"code": str, "payload": any, "output_limit": int, "value_limit": int,
     "harness": optional module name, "sys_path": optional list of dirs}

runs ``code`` with ``payload`` in scope, and writes one result line to the
original stdout, prefixed with ``RESULT_MARKER``.

With ``harness``, the runner imports that module and builds ``Harness(payload)``
before the code runs, adds ``harness.scope()`` to the code's globals, and puts
``harness.finish()`` in the result afterwards, whether or not the code raised.
That's how a game step gets a booted emulator in and a save state out, without
the step's own output being squeezed by the limits on the code's ``result``.

The snippet's own stdout and stderr (fds 1 and 2, so ``os.write`` and child
processes too) are pointed at unnamed temp files before it runs, so nothing it
prints can be mistaken for the result. A snippet that goes looking for the saved
result fd can still corrupt the protocol; the host treats that as a crash. This
is about keeping the result readable, not about safety -- the container is the
wall.

It only uses the standard library, and runs unchanged outside the container,
which is how the protocol is unit-tested.
"""

import importlib
import json
import os
import sys
import tempfile
import time
import traceback

RESULT_MARKER = "\x1egb-agent-result:"
TRACEBACK_LIMIT = 8_000
CODE_ROOT = os.path.dirname(os.path.abspath(__file__))  # where the image puts gb_agent/


def _capture(fd: int):
    """Point ``fd`` at a fresh unnamed temp file; return that file."""
    f = tempfile.TemporaryFile()
    os.dup2(f.fileno(), fd)
    return f


def _read_capped(f, limit: int) -> tuple[str, int]:
    """First ``limit`` bytes of a capture file, decoded, plus its full size."""
    size = os.fstat(f.fileno()).st_size
    f.seek(0)
    return f.read(limit).decode("utf-8", errors="replace"), size


def _encode_value(value, limit: int):
    """The snippet's ``result``, as JSON if it can be, cut to ``limit`` chars."""
    try:
        text = json.dumps(value)
        kind = "json"
    except (TypeError, ValueError):
        text = repr(value)
        kind = "repr"
    if len(text) > limit:
        return {"kind": "truncated", "text": text[:limit]}
    return {"kind": kind, "text": text}


def _describe(e: BaseException) -> dict:
    return {
        "type": type(e).__name__,
        "message": str(e)[:TRACEBACK_LIMIT],
        "traceback": traceback.format_exc()[-TRACEBACK_LIMIT:],
    }


def main() -> None:
    request = json.loads(sys.stdin.read())
    sys.stdin.close()
    output_limit = int(request.get("output_limit", 16_000))
    value_limit = int(request.get("value_limit", 16_000))
    sys.path[:0] = request.get("sys_path") or [CODE_ROOT]

    sys.stdout.flush()
    sys.stderr.flush()
    result_fd = os.dup(1)
    out = _capture(1)
    err = _capture(2)

    scope = {"__name__": "__sandbox__", "payload": request.get("payload")}
    harness = harness_out = harness_error = error = None
    if request.get("harness"):
        try:
            module = importlib.import_module(request["harness"])
            harness = module.Harness(request.get("payload"))
            scope.update(harness.scope())
        except BaseException as e:
            harness_error = _describe(e)

    started = time.monotonic()
    if harness_error is None:
        try:
            exec(compile(request["code"], "<script>", "exec"), scope)
        except BaseException as e:  # SystemExit and KeyboardInterrupt are errors too
            error = _describe(e)
    duration = time.monotonic() - started

    if harness is not None:
        try:
            harness_out = harness.finish()
        except BaseException as e:
            harness_error = _describe(e)

    try:
        sys.stdout.flush()
        sys.stderr.flush()
    except OSError:
        pass  # a full scratch disk; what was written is still readable

    stdout, stdout_size = _read_capped(out, output_limit)
    stderr, stderr_size = _read_capped(err, output_limit)
    result = {
        "error": error,
        "value": _encode_value(scope.get("result"), value_limit) if "result" in scope else None,
        "stdout": stdout,
        "stdout_bytes": stdout_size,
        "stderr": stderr,
        "stderr_bytes": stderr_size,
        "duration": duration,
        "harness": harness_out,
        "harness_error": harness_error,
    }
    line = memoryview((RESULT_MARKER + json.dumps(result) + "\n").encode())
    while line:
        line = line[os.write(result_fd, line):]
    # Skip interpreter shutdown, so the snippet's atexit hooks and leftover
    # threads can't run or write after the result.
    os._exit(0)


if __name__ == "__main__":
    main()
