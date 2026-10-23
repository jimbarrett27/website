"""The sandbox runner's stdin/stdout protocol, run directly (no Docker needed)."""

import json
import subprocess
import sys

from gb_agent.sandbox.run import IMAGE_DIR, _from_runner, parse_result

RUNNER = IMAGE_DIR / "runner.py"


def run(code: str, payload=None, **limits) -> dict:
    request = json.dumps({"code": code, "payload": payload, **limits})
    proc = subprocess.run([sys.executable, "-I", str(RUNNER)], input=request.encode(),
                          capture_output=True, timeout=30)
    assert proc.returncode == 0
    result = parse_result(proc.stdout)
    assert result is not None, proc.stdout
    return result


def test_payload_in_and_result_out():
    result = _from_runner(run("result = {'doubled': payload * 2}", payload=21))
    assert result.status == "ok"
    assert result.value == {"doubled": 42}


def test_no_result_global_means_no_value():
    assert run("x = 1")["value"] is None


def test_unserialisable_result_comes_back_as_repr():
    result = _from_runner(run("result = object()"))
    assert result.value.startswith("<object object")


def test_exception_is_reported_not_raised():
    result = _from_runner(run("print('before')\nraise ValueError('nope')"))
    assert result.status == "error"
    assert result.error["type"] == "ValueError"
    assert "nope" in result.error["traceback"]
    assert result.stdout == "before\n"


def test_sys_exit_is_an_error_too():
    assert run("import sys; sys.exit(3)")["error"]["type"] == "SystemExit"


def test_prints_cannot_forge_a_result():
    # The snippet's stdout is captured, so a fake marker line is just output.
    fake = '"\\x1egb-agent-result:" + \'{"error": null, "value": null}\''
    result = run(f"print({fake})\nresult = 'real'")
    assert json.loads(result["value"]["text"]) == "real"
    assert "gb-agent-result" in result["stdout"]


def test_raw_fd_writes_and_child_processes_are_captured():
    code = (
        "import os, subprocess, sys\n"
        "os.write(1, b'raw\\n')\n"
        "subprocess.run([sys.executable, '-c', 'print(\"child\")'])\n"
    )
    assert run(code)["stdout"] == "raw\nchild\n"


def test_output_is_capped_but_full_size_reported():
    result = run("print('x' * 100_000)", output_limit=1_000)
    assert len(result["stdout"]) == 1_000
    assert result["stdout_bytes"] == 100_001


def test_big_result_is_truncated():
    result = _from_runner(run("result = 'y' * 50_000", value_limit=100))
    assert result.value_truncated
    assert len(result.value) == 100


def test_atexit_hooks_do_not_run():
    code = "import atexit\natexit.register(lambda: print('late'))"
    proc = subprocess.run(
        [sys.executable, "-I", str(RUNNER)],
        input=json.dumps({"code": code}).encode(), capture_output=True, timeout=30,
    )
    assert b"late" not in proc.stdout


def test_parse_result_without_marker_is_none():
    assert parse_result(b"just some output\n") is None
    assert parse_result(b"\x1egb-agent-result:{broken") is None
