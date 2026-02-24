# ─────────────────────────────────────────────────────────────────
# Multi-architecture RPi test image
#
# Tests MeshPi package installation across different RPi architectures
# Supports arm32v6, arm32v7, arm64v8, and x86_64 for comparison
#
# Build args:
#   BASE_IMAGE: Python base image for target architecture
#   PYTHON_VERSION: Python version to test (default: 3.11)
#   ARCH: Target architecture identifier
# ─────────────────────────────────────────────────────────────────
ARG BASE_IMAGE=python:3.11-slim-bullseye
ARG PYTHON_VERSION=3.11
ARG ARCH=x86_64

FROM ${BASE_IMAGE}

LABEL maintainer="Softreck <info@softreck.dev>"
LABEL description="MeshPi multi-architecture test runner"
LABEL version="0.1.0"
LABEL architecture="${ARCH}"

# Install system dependencies needed for testing
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    wget \
    git \
    unzip \
    file \
    lsb-release \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install pip and ensure it's up to date
RUN python -m pip install --upgrade pip setuptools wheel

# Copy test scripts first (cached layer)
COPY docker/test-rpi/test-installation.py /app/test-installation.py
COPY docker/test-rpi/aggregate-results.py /app/aggregate-results.py
COPY docker/test-rpi/test-utils.py /app/test-utils.py

# Copy package files
COPY pyproject.toml README.md LICENSE ./

# Test different installation methods
RUN echo "=== Testing pip installation from PyPI ===" && \
    pip install meshpi && \
    python -c "import meshpi; print(f'MeshPi version: {meshpi.__version__}')" && \
    pip uninstall -y meshpi

RUN echo "=== Testing pip installation from source ===" && \
    pip install -e . && \
    python -c "import meshpi; print(f'MeshPi version: {meshpi.__version__}')" && \
    pip uninstall -y meshpi

RUN echo "=== Testing installation with optional dependencies ===" && \
    pip install "meshpi[llm,dev]" && \
    python -c "import meshpi; print(f'MeshPi version: {meshpi.__version__}')" && \
    python -c "import litellm; print('LLM dependencies OK')" && \
    python -c "import pytest; print('Dev dependencies OK')"

# Create test results directory
RUN mkdir -p /app/test-results

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV MESHPI_TEST_ARCH=${ARCH}
ENV MESHPI_TEST_PYTHON_VERSION=${PYTHON_VERSION}

# Default command - run installation tests
CMD ["python", "test-installation.py", "--verbose"]
