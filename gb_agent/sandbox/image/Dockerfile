# The sandbox every agent-written script runs in. Python plus PyBoy, nothing else.
# The host adds the real walls at `docker run` time (no network, read-only root,
# caps dropped, resource limits); see gb_agent/sandbox/run.py.
FROM python:3.12-slim

RUN pip install --no-cache-dir pyboy==2.7.0 \
    && useradd --uid 10001 --no-create-home --shell /usr/sbin/nologin sandbox

COPY runner.py /opt/gb_agent/runner.py

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOME=/tmp

USER 10001:10001
WORKDIR /tmp
ENTRYPOINT ["python", "-I", "/opt/gb_agent/runner.py"]
