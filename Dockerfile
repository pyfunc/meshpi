# MeshPi Docker Image for Testing
# Supports both host and client modes

FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    iputils-ping \
    net-tools \
    dbus \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy package files
COPY pyproject.toml ./
COPY meshpi ./meshpi/
COPY README.md ./
COPY VERSION ./

# Install the package
RUN pip install --no-cache-dir -e .

# Create meshpi directory for keys and config
RUN mkdir -p /root/.meshpi

# Default environment
ENV MESHPI_HOST=0.0.0.0
ENV MESHPI_PORT=7422

# Expose port for host mode
EXPOSE 7422

# Default command - can be overridden
CMD ["meshpi", "--help"]