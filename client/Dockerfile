# ─────────────────────────────────────────────────────────────────
# MeshPi CLIENT image — simulates a Raspberry Pi client
#
# Used for integration testing without real hardware.
# Runs: meshpi scan / meshpi daemon in a container.
#
# Does NOT apply system-level config (user/wifi/locale) — instead
# it logs what would be applied, enabling full protocol testing.
#
# Build:  docker build -t meshpi-client -f docker/client/Dockerfile .
# ─────────────────────────────────────────────────────────────────
FROM python:3.12-slim-bookworm AS builder

WORKDIR /build
COPY pyproject.toml README.md LICENSE ./
COPY meshpi/ ./meshpi/
RUN pip install --no-cache-dir build && python -m build --wheel


FROM python:3.12-slim-bookworm

LABEL maintainer="Softreck <info@softreck.dev>"
LABEL description="MeshPi Client — RPi simulator for integration testing"
LABEL version="0.2.0"

RUN apt-get update && apt-get install -y --no-install-recommends \
    iputils-ping \
    curl \
    hostname \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /build/dist/*.whl /tmp/
RUN pip install --no-cache-dir /tmp/*.whl websockets && rm /tmp/*.whl

RUN mkdir -p /root/.meshpi && chmod 700 /root/.meshpi

COPY docker/client/entrypoint.sh /entrypoint.sh
COPY docker/client/fake_applier.py /app/fake_applier.py
RUN chmod +x /entrypoint.sh

# Patch applier to simulate-only mode in Docker
ENV MESHPI_DRY_RUN=1
ENV PYTHONUNBUFFERED=1

# Client identifier (becomes device_id in registry)
ENV MESHPI_DEVICE_ID=""

VOLUME ["/root/.meshpi"]

ENTRYPOINT ["/entrypoint.sh"]
CMD ["daemon"]
