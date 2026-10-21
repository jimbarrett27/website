"""Run untrusted code in a locked-down, throwaway Docker container.

Each call starts a fresh container from the sandbox image, sends the code and a
JSON payload on stdin, and reads one result line back from stdout. Nothing from
the host is mounted unless asked for, and then only read-only, so the container
has no way to leave anything behind: stdin in, stdout out.

The walls are all set here, at ``docker run`` time:

- no network, read-only root filesystem, a small size-capped ``/tmp``
- a non-root user, every capability dropped, no privilege escalation
- memory (with swap equal to it, so no swapping), CPU and process-count caps
- a hard wall-clock timeout; the container is killed, not just the CLI
- ``--log-driver none``, or Docker would keep everything the code prints on disk
- an empty environment: ``docker run`` passes none of the host's variables
"""

import hashlib
import json
import subprocess
import threading
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

IMAGE_DIR = Path(__file__).parent / "image"
BUILD_CONTEXT = IMAGE_DIR.parent.parent  # gb_agent/
IMAGE_NAME = "gb-agent-sandbox"
RESULT_MARKER = "\x1egb-agent-result:"  # must match image/runner.py
SANDBOX_USER = "10001:10001"
DOCKER_CLI_TIMEOUT_S = 30

Status = Literal["ok", "error", "timeout", "oom", "crashed"]


@dataclass(frozen=True)
class SandboxLimits:
    timeout_s: float = 30.0
    memory_mb: int = 512
    cpus: float = 1.0
    pids: int = 64
    tmpfs_mb: int = 64
    output_limit: int = 16_000  # chars of stdout/stderr returned, each
    value_limit: int = 16_000  # chars of the snippet's `result`
    read_limit: int = 8_000_000  # bytes of container stdout the host will hold


@dataclass
class SandboxResult:
    status: Status
    value: Any = None  # the snippet's `result` global, if it set one
    value_truncated: bool = False
    stdout: str = ""
    stderr: str = ""
    stdout_bytes: int = 0  # full sizes, so a caller can say what was cut
    stderr_bytes: int = 0
    error: dict | None = None  # type, message, traceback
    harness: dict | None = None  # the harness's finish() output, if one ran
    harness_error: dict | None = None  # the harness itself failed, not the code
    exit_code: int | None = None
    duration_s: float = 0.0
    detail: str = ""  # why, for anything but ok/error
    diagnostics: str = field(default="", repr=False)  # docker's own stderr


def image_files() -> list[Path]:
    """Everything that goes into the image (mirrors gb_agent/.dockerignore)."""
    return sorted([
        BUILD_CONTEXT / ".dockerignore",
        BUILD_CONTEXT / "__init__.py",
        IMAGE_DIR / "Dockerfile",
        IMAGE_DIR / "runner.py",
        *(BUILD_CONTEXT / "emulator").glob("*.py"),
    ])


def image_tag() -> str:
    """Tag the image by its contents, so any change to it means a rebuild."""
    digest = hashlib.sha256()
    for path in image_files():
        digest.update(str(path.relative_to(BUILD_CONTEXT)).encode())
        digest.update(path.read_bytes())
    return f"{IMAGE_NAME}:{digest.hexdigest()[:12]}"


def build_image() -> str:
    """Build the sandbox image if this version isn't built yet; return its tag."""
    tag = image_tag()
    exists = subprocess.run(
        ["docker", "image", "inspect", tag], capture_output=True
    ).returncode == 0
    if not exists:
        subprocess.run(
            ["docker", "build", "-q", "-t", tag,
             "-f", str(IMAGE_DIR / "Dockerfile"), str(BUILD_CONTEXT)],
            check=True, capture_output=True,
        )
    return tag


def docker_args(name: str, image: str, limits: SandboxLimits,
                read_only_mounts: dict[Path, str]) -> list[str]:
    args = [
        "docker", "run", "-i",
        "--name", name,
        "--network", "none",
        "--read-only",
        "--tmpfs", f"/tmp:rw,noexec,nosuid,nodev,size={limits.tmpfs_mb}m",
        "--user", SANDBOX_USER,
        "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges",
        "--memory", f"{limits.memory_mb}m",
        "--memory-swap", f"{limits.memory_mb}m",
        "--cpus", str(limits.cpus),
        "--pids-limit", str(limits.pids),
        "--ulimit", "nofile=256:256",
        "--log-driver", "none",
    ]
    for host_path, container_path in read_only_mounts.items():
        args += ["--mount", f"type=bind,src={Path(host_path).resolve()},"
                            f"dst={container_path},readonly"]
    return args + [image]


def _read_capped(stream, limit: int, sink: bytearray) -> None:
    """Keep up to ``limit`` bytes in ``sink``, and read and discard the rest.

    Discarding keeps code that floods stdout from filling the host's memory.
    The reading has to carry on regardless: if the pipe backs up, Docker can't
    finish tearing the container down, and ``docker kill`` hangs.
    """
    while chunk := stream.read(65536):
        if len(sink) < limit:
            sink.extend(chunk[: limit - len(sink)])


def parse_result(raw: bytes) -> dict | None:
    """The runner's result line from container stdout, or None if there isn't one."""
    text = raw.decode("utf-8", errors="replace")
    _, marker, rest = text.rpartition(RESULT_MARKER)
    if not marker:
        return None
    try:
        return json.loads(rest.strip())
    except json.JSONDecodeError:
        return None


def _from_runner(result: dict) -> SandboxResult:
    value, truncated = None, False
    if result.get("value") is not None:
        kind, text = result["value"]["kind"], result["value"]["text"]
        truncated = kind == "truncated"
        value = json.loads(text) if kind == "json" else text
    return SandboxResult(
        status="error" if result.get("error") else "ok",
        value=value,
        value_truncated=truncated,
        stdout=result.get("stdout", ""),
        stderr=result.get("stderr", ""),
        stdout_bytes=result.get("stdout_bytes", 0),
        stderr_bytes=result.get("stderr_bytes", 0),
        error=result.get("error"),
        harness=result.get("harness"),
        harness_error=result.get("harness_error"),
    )


def _docker(*args: str) -> subprocess.CompletedProcess:
    """A housekeeping docker command that can't hang the caller."""
    try:
        return subprocess.run(["docker", *args], capture_output=True, text=True,
                              timeout=DOCKER_CLI_TIMEOUT_S)
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(args, returncode=-1, stdout="", stderr="timed out")


def _remove(name: str) -> bool:
    """Force-remove the container; return whether the kernel OOM-killed it."""
    inspected = _docker("inspect", "-f", "{{.State.OOMKilled}}", name)
    _docker("rm", "-f", name)
    return inspected.stdout.strip() == "true"


def run_in_sandbox(
    code: str,
    payload: Any = None,
    *,
    limits: SandboxLimits = SandboxLimits(),
    read_only_mounts: dict[Path, str] | None = None,
    harness: str | None = None,
    image: str | None = None,
) -> SandboxResult:
    """Run ``code`` in a fresh sandbox container and report what happened.

    Inside, ``payload`` is in scope, and whatever the code assigns to a global
    named ``result`` comes back as ``SandboxResult.value`` (JSON if it can be,
    otherwise its repr). Never raises for anything the code does; failures come
    back as a status.

    ``read_only_mounts`` maps host paths to container paths. The code runs as
    uid 10001, not as you, so mounted files must be world-readable.

    ``harness`` names a module in the image (such as ``gb_agent.emulator.harness``)
    whose ``Harness`` wraps the code; see image/runner.py.
    """
    name = f"gb-agent-{uuid.uuid4().hex[:12]}"
    request = json.dumps({
        "code": code,
        "payload": payload,
        "harness": harness,
        "output_limit": limits.output_limit,
        "value_limit": limits.value_limit,
    }).encode()

    started = time.monotonic()
    proc = subprocess.Popen(
        docker_args(name, image or build_image(), limits, read_only_mounts or {}),
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    out, err = bytearray(), bytearray()
    readers = [
        threading.Thread(target=_read_capped, args=(proc.stdout, limits.read_limit, out)),
        threading.Thread(target=_read_capped, args=(proc.stderr, 64_000, err)),
    ]
    for reader in readers:
        reader.daemon = True
        reader.start()

    timed_out = False
    try:
        try:
            proc.stdin.write(request)
            proc.stdin.close()
        except BrokenPipeError:
            pass  # the container died before reading; the exit code says why
        try:
            proc.wait(timeout=limits.timeout_s)
        except subprocess.TimeoutExpired:
            timed_out = True
            _docker("kill", name)
            proc.kill()
            proc.wait()
    finally:
        oom = _remove(name)
    for reader in readers:
        reader.join(timeout=5)
    duration = time.monotonic() - started
    diagnostics = err.decode("utf-8", errors="replace")

    # A result from the runner wins over the OOM flag: the flag is also set when
    # only a child process was killed, and then the code's own error says more.
    parsed = parse_result(bytes(out)) if proc.returncode == 0 else None
    if timed_out:
        result = SandboxResult(status="timeout",
                               detail=f"killed after {limits.timeout_s:g}s")
    elif parsed is not None:
        result = _from_runner(parsed)
    elif oom:
        result = SandboxResult(status="oom",
                               detail=f"exceeded {limits.memory_mb} MB of memory")
    else:
        result = SandboxResult(
            status="crashed",
            detail=f"exited {proc.returncode} without a readable result",
        )
    result.exit_code = proc.returncode
    result.duration_s = duration
    result.diagnostics = diagnostics
    return result
