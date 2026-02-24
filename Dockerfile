# ─────────────────────────────────────────────────────────────────
# MeshPi HOST image
# Runs: meshpi host (FastAPI + WebSocket + mDNS advertisement)
#
# Build:  docker build -t meshpi-host -f docker/host/Dockerfile .
# Run:    docker run -p 7422:7422 meshpi-host
# ─────────────────────────────────────────────────────────────────
FROM python:3.12-slim-bookworm AS builder

WORKDIR /build
COPY pyproject.toml README.md LICENSE ./
COPY meshpi/ ./meshpi/

RUN pip install --no-cache-dir build && \
    python -m build --wheel && \
    ls dist/


FROM python:3.12-slim-bookworm

LABEL maintainer="Softreck <info@softreck.dev>"
LABEL description="MeshPi Host — encrypted RPi fleet configuration server"
LABEL version="0.2.0"
LABEL license="Apache-2.0"

# Runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    iputils-ping \
    avahi-daemon \
    avahi-utils \
    libnss-mdns \
    dbus \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy built wheel from builder stage
COPY --from=builder /build/dist/*.whl /tmp/
RUN pip install --no-cache-dir /tmp/*.whl "meshpi[llm]" 2>/dev/null || \
    pip install --no-cache-dir /tmp/*.whl && \
    rm /tmp/*.whl

# Create meshpi config directory
RUN mkdir -p /root/.meshpi && chmod 700 /root/.meshpi

# Copy entrypoint
COPY docker/host/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Config volume — mount your config.env here
VOLUME ["/root/.meshpi"]

# Default environment
ENV MESHPI_PORT=7422
ENV MESHPI_BIND=0.0.0.0
ENV PYTHONUNBUFFERED=1

EXPOSE 7422

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:7422/health', timeout=4).raise_for_status()"

ENTRYPOINT ["/entrypoint.sh"]
CMD ["host"]
