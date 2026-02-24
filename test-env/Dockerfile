# ─────────────────────────────────────────────────────────────────
# MeshPi TEST image
# Runs pytest test suite in an isolated container.
#
# Build:  docker build -t meshpi-test -f docker/test-env/Dockerfile .
# Run:    docker run --rm meshpi-test
# ─────────────────────────────────────────────────────────────────
FROM python:3.12-slim-bookworm

LABEL description="MeshPi test runner"

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install package + test deps first (cached layer)
COPY pyproject.toml README.md LICENSE ./
RUN pip install --no-cache-dir -e ".[dev]" websockets

# Copy source + tests (separate layer so test changes don't reinstall deps)
COPY meshpi/ ./meshpi/
COPY tests/   ./tests/

ENV PYTHONUNBUFFERED=1

CMD ["python", "-m", "pytest", "tests/", "-v", "--tb=short", "--color=yes"]
