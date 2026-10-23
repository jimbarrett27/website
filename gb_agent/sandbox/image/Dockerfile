# The sandbox every agent-written script runs in: Python, PyBoy, and gb_agent's
# emulator package. The host adds the real walls at `docker run` time (no network,
# read-only root, caps dropped, resource limits); see gb_agent/sandbox/run.py.
#
# Built with gb_agent/ as the context (see IMAGE_FILES in run.py). Versions match
# the host's, since the host replays every step and expects identical states.
FROM python:3.12-slim

RUN pip install --no-cache-dir pyboy==2.7.0 numpy==2.5.3 pillow==12.3.0 \
    && useradd --uid 10001 --no-create-home --shell /usr/sbin/nologin sandbox

COPY sandbox/image/runner.py /opt/gb_agent/runner.py
COPY __init__.py /opt/gb_agent/gb_agent/__init__.py
COPY emulator/ /opt/gb_agent/gb_agent/emulator/

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOME=/tmp

USER 10001:10001
WORKDIR /tmp
ENTRYPOINT ["python", "-I", "/opt/gb_agent/runner.py"]
