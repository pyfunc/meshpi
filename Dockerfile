"""
MeshPi Host Docker Image

Usage:
    docker build -t meshpi-host .
    docker run -p 7422:7422 meshpi-host

Environment Variables:
    MESHPI_PORT       - Host port (default: 7422)
    MESHPI_BIND       - Bind address (default: 0.0.0.0)
    MESHPI_CONFIG_DIR - Config directory (default: /app/config)
"""

FROM python:3.11-slim

LABEL maintainer="MeshPi"
LABEL version="0.2.0"
LABEL description="MeshPi Host Service for Raspberry Pi Fleet Management"

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV MESHPI_PORT=7422
ENV MESHPI_BIND=0.0.0.0
ENV MESHPI_CONFIG_DIR=/app/config

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    avahi-daemon \
    avahi-utils \
    libnss-mdns \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Create non-root user
RUN useradd -m -u 1000 meshpi && \
    mkdir -p /app/config /app/data && \
    chown -R meshpi:meshpi /app

# Install Python dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir -e . && \
    pip install --no-cache-dir prometheus-client pyyaml

# Copy application code
COPY --chown=meshpi:meshpi . .

# Switch to non-root user
USER meshpi

# Expose ports
EXPOSE 7422

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:7422/health || exit 1

# Run the host service
CMD ["python", "-m", "meshpi.host"]