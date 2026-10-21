"""Code that tries to escape or abuse the sandbox, which must fail cleanly.

Each test runs real code in a real container, so these need Docker and the
sandbox image (built on first use, which needs the network once).
"""

import os
import shutil
import subprocess

import pytest

from gb_agent.sandbox import SandboxLimits, build_image, run_in_sandbox
from gb_agent.sandbox.run import docker_args


def _docker_available() -> bool:
    if shutil.which("docker") is None:
        return False
    return subprocess.run(["docker", "info"], capture_output=True).returncode == 0


pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not _docker_available(), reason="needs a working Docker"),
]

QUICK = SandboxLimits(timeout_s=5)
IMAGE_ENV = {
    "PATH", "HOSTNAME", "HOME", "LANG", "GPG_KEY", "PYTHON_VERSION", "PYTHON_SHA256",
    "PYTHONDONTWRITEBYTECODE", "PYTHONUNBUFFERED",
}


@pytest.fixture(scope="module")
def image():
    return build_image()


def run(image, code, payload=None, limits=QUICK, **kwargs):
    return run_in_sandbox(code, payload, limits=limits, image=image, **kwargs)


def test_a_normal_script_works(image):
    result = run(image, "import pyboy\nprint('hello')\nresult = payload + 1", 41)
    assert result.status == "ok", result
    assert result.value == 42
    assert result.stdout == "hello\n"


def test_no_network(image):
    code = (
        "import socket\n"
        "errors = []\n"
        "for target in [('1.1.1.1', 53), ('8.8.8.8', 443)]:\n"
        "    try:\n"
        "        socket.create_connection(target, timeout=2)\n"
        "    except OSError as e:\n"
        "        errors.append(type(e).__name__)\n"
        "try:\n"
        "    socket.getaddrinfo('github.com', 443)\n"
        "except OSError as e:\n"
        "    errors.append(type(e).__name__)\n"
        "interfaces = [l.split(':')[0].strip() for l in open('/proc/net/dev').readlines()[2:]]\n"
        "result = {'errors': errors, 'interfaces': interfaces}\n"
    )
    result = run(image, code)
    assert result.status == "ok", result
    assert len(result.value["errors"]) == 3
    assert result.value["interfaces"] == ["lo"]


def test_root_filesystem_is_read_only(image):
    code = (
        "blocked = []\n"
        "for path in ['/x', '/etc/x', '/opt/gb_agent/runner.py', '/usr/local/lib/x', '/var/x']:\n"
        "    try:\n"
        "        open(path, 'w').write('x')\n"
        "    except OSError:\n"
        "        blocked.append(path)\n"
        "open('/tmp/scratch', 'w').write('fine')\n"
        "result = blocked\n"
    )
    result = run(image, code)
    assert result.status == "ok", result
    assert len(result.value) == 5


def test_scratch_space_is_capped(image):
    code = (
        "chunk = b'x' * 1024 * 1024\n"
        "written = 0\n"
        "try:\n"
        "    with open('/tmp/fill', 'wb') as f:\n"
        "        for _ in range(500):\n"
        "            f.write(chunk)\n"
        "            written += 1\n"
        "except OSError as e:\n"
        "    result = {'mb': written, 'error': e.errno}\n"
    )
    result = run(image, code, limits=SandboxLimits(timeout_s=10, tmpfs_mb=16))
    assert result.status == "ok", result
    assert result.value["mb"] <= 16


def test_scratch_space_is_not_executable(image):
    code = (
        "import os, subprocess\n"
        "open('/tmp/run.sh', 'w').write('#!/bin/sh\\necho escaped\\n')\n"
        "os.chmod('/tmp/run.sh', 0o755)\n"
        "subprocess.run(['/tmp/run.sh'])\n"
    )
    result = run(image, code)
    assert result.status == "error"
    assert result.error["type"] == "PermissionError"


def test_host_home_and_processes_are_invisible(image):
    code = (
        "import os\n"
        "comms = []\n"
        "for pid in os.listdir('/proc'):\n"
        "    if pid.isdigit():\n"
        "        try:\n"
        "            comms.append(open(f'/proc/{pid}/comm').read().strip())\n"
        "        except OSError:\n"
        "            pass\n"
        "result = {'home': os.path.exists(os.path.expanduser('~jim')) or os.path.exists('/home/jim'),\n"
        "          'home_dir': os.listdir('/home'), 'processes': comms}\n"
    )
    result = run(image, code)
    assert result.status == "ok", result
    assert result.value["home"] is False
    assert result.value["home_dir"] == []
    assert "dockerd" not in result.value["processes"]
    assert len(result.value["processes"]) < 5


def test_host_environment_is_not_passed_in(image, monkeypatch):
    monkeypatch.setenv("GB_AGENT_CANARY_SECRET", "do-not-leak")
    result = run(image, "import os\nresult = dict(os.environ)")
    assert result.status == "ok", result
    assert "do-not-leak" not in str(result.value)
    # Only what the image itself sets. GPG_KEY is the public ID of the key
    # CPython releases are signed with, set by the official Python image.
    assert set(result.value) <= IMAGE_ENV, set(result.value) - IMAGE_ENV


def test_unprivileged(image):
    code = (
        "import os\n"
        "status = dict(l.split(':\\t', 1) for l in open('/proc/self/status').read().splitlines() if ':\\t' in l)\n"
        "result = {'uid': os.getuid(), 'cap_eff': status['CapEff'].strip(),\n"
        "          'cap_bnd': status['CapBnd'].strip(), 'nnp': status['NoNewPrivs'].strip()}\n"
    )
    result = run(image, code)
    assert result.status == "ok", result
    assert result.value["uid"] == 10001
    assert int(result.value["cap_eff"], 16) == 0
    assert int(result.value["cap_bnd"], 16) == 0
    assert result.value["nnp"] == "1"


def test_read_only_mounts_can_be_read_not_written(image, tmp_path):
    # The sandbox user isn't you, so mounts have to be world-readable.
    tmp_path.chmod(0o755)
    (tmp_path / "rom.gbc").write_bytes(b"pretend rom")
    (tmp_path / "rom.gbc").chmod(0o666)  # writable by anyone, so only the mount stops it
    code = (
        "data = open('/rom/rom.gbc', 'rb').read()\n"
        "try:\n"
        "    open('/rom/rom.gbc', 'wb').write(b'overwritten')\n"
        "    wrote = True\n"
        "except OSError:\n"
        "    wrote = False\n"
        "result = {'data': data.decode(), 'wrote': wrote}\n"
    )
    result = run(image, code, read_only_mounts={tmp_path: "/rom"})
    assert result.status == "ok", result
    assert result.value == {"data": "pretend rom", "wrote": False}
    assert (tmp_path / "rom.gbc").read_bytes() == b"pretend rom"


def test_process_count_is_capped(image):
    code = (
        "import os, time\n"
        "forked = 0\n"
        "try:\n"
        "    while forked < 1000:\n"
        "        if os.fork() == 0:\n"
        "            time.sleep(60)\n"
        "            os._exit(0)\n"
        "        forked += 1\n"
        "except OSError as e:\n"
        "    result = {'forked': forked, 'error': type(e).__name__}\n"
    )
    limits = SandboxLimits(timeout_s=10, pids=32)
    result = run(image, code, limits=limits)
    assert result.status == "ok", result
    assert result.value["forked"] < 32


def test_fork_bomb_is_killed(image):
    code = (
        "import os\n"
        "while True:\n"
        "    try:\n"
        "        os.fork()\n"
        "    except OSError:\n"
        "        pass\n"
    )
    result = run(image, code, limits=SandboxLimits(timeout_s=3, pids=32))
    assert result.status == "timeout", result
    assert result.duration_s < 15


def test_memory_is_capped(image):
    result = run(image, "hog = b'x' * (2 * 1024 ** 3)",
                 limits=SandboxLimits(timeout_s=15, memory_mb=256))
    assert result.status in ("oom", "error"), result
    if result.status == "error":
        assert result.error["type"] == "MemoryError"


def test_infinite_loop_is_killed(image):
    result = run(image, "while True:\n    pass", limits=SandboxLimits(timeout_s=3))
    assert result.status == "timeout", result
    assert result.duration_s < 10


def test_endless_printing_is_bounded(image):
    limits = SandboxLimits(timeout_s=5, output_limit=2_000, tmpfs_mb=16)
    result = run(image, "while True:\n    print('x' * 1000)", limits=limits)
    # Either the capture fills the scratch space and print fails, or time runs out.
    assert result.status in ("error", "timeout"), result
    assert len(result.stdout) <= 2_000


def test_flooding_the_result_pipe_is_bounded(image):
    # Write straight to every inherited fd, including the runner's saved stdout.
    code = (
        "import os\n"
        "block = b'z' * 65536\n"
        "while True:\n"
        "    for fd in range(3, 10):\n"
        "        try:\n"
        "            os.write(fd, block)\n"
        "        except OSError:\n"
        "            pass\n"
    )
    limits = SandboxLimits(timeout_s=4, read_limit=1_000_000)
    result = run(image, code, limits=limits)
    assert result.status in ("timeout", "crashed"), result


def test_containers_are_removed_afterwards(image):
    run(image, "result = 1")
    run(image, "while True:\n    pass", limits=SandboxLimits(timeout_s=2))
    leftover = subprocess.run(
        ["docker", "ps", "-aq", "--filter", "name=gb-agent-"],
        capture_output=True, text=True,
    ).stdout.split()
    assert leftover == []


def test_nothing_is_logged_by_docker(image):
    # With the default log driver Docker keeps every byte printed on disk.
    args = docker_args("probe", image, QUICK, {})
    assert args[args.index("--log-driver") + 1] == "none"
