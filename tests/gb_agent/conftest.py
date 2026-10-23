import shutil
import subprocess
from pathlib import Path

import pytest

from gb_agent.emulator import power_on_state
from gb_agent.games import SILVER

TEST_ROM = Path(__file__).parent / "roms" / "rtc3test.gb"


def docker_available() -> bool:
    if shutil.which("docker") is None:
        return False
    return subprocess.run(["docker", "info"], capture_output=True).returncode == 0


needs_docker = [
    pytest.mark.integration,
    pytest.mark.skipif(not docker_available(), reason="needs a working Docker"),
]


@pytest.fixture(scope="session")
def image():
    from gb_agent.sandbox import build_image
    return build_image()


@pytest.fixture(scope="session")
def test_rom() -> bytes:
    return TEST_ROM.read_bytes()


@pytest.fixture(scope="session")
def test_start(test_rom) -> bytes:
    """One saved power-on state, shared, since every boot stamps in the time."""
    return power_on_state(test_rom)


@pytest.fixture(scope="session")
def silver_rom() -> bytes:
    if not SILVER.rom.exists():
        pytest.skip(f"no Pokemon Silver ROM at {SILVER.rom}")
    return SILVER.rom.read_bytes()
