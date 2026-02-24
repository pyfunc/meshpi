# ─────────────────────────────────────────────────────────────────────────────
# MeshPi Makefile
# ─────────────────────────────────────────────────────────────────────────────

.DEFAULT_GOAL := help
.PHONY: help build test test-unit test-integration up down clean logs shell-host shell-client ps wheel publish install venv env-host env-dev

COMPOSE = docker compose
IMAGE_HOST   = meshpi-host:latest
IMAGE_CLIENT = meshpi-client:latest
IMAGE_TEST   = meshpi-test:latest

# Project info
PROJECT_NAME := meshpi
VERSION := $(shell cat VERSION 2>/dev/null || echo "0.1.5")
PYTHON := .venv/bin/python

# ── Help ──────────────────────────────────────────────────────────────────────
help:
	@echo ""
	@echo "  MeshPi — Development & Deployment Commands"
	@echo "  ──────────────────────────────────────────────────────────"
	@echo ""
	@echo "  Setup & Installation:"
	@echo "    make venv           Create virtual environment"
	@echo "    make install        Install package in development mode"
	@echo "    make install-dev    Install with dev dependencies"
	@echo "    make env-host       Create sample .env for host"
	@echo ""
	@echo "  Testing:"
	@echo "    make test           Run all unit tests"
	@echo "    make test-v         Run tests with verbose output"
	@echo "    make test-cov       Run tests with coverage report"
	@echo "    make test-docker    Run tests inside Docker"
	@echo "    make test-int       Run integration tests (requires host)"
	@echo ""
	@echo "  Docker:"
	@echo "    make build          Build all Docker images"
	@echo "    make up             Start host + 2 clients"
	@echo "    make up-host        Start host only"
	@echo "    make down           Stop and remove containers"
	@echo "    make logs           Follow all service logs"
	@echo "    make shell-host     Open shell in host container"
	@echo ""
	@echo "  Package & Publish:"
	@echo "    make wheel          Build Python .whl package"
	@echo "    make build-dist     Build source dist and wheel"
	@echo "    make publish        Publish to PyPI (requires PYPI_TOKEN)"
	@echo "    make publish-test   Publish to TestPyPI"
	@echo ""
	@echo "  Utilities:"
	@echo "    make clean          Remove build artifacts"
	@echo "    make lint           Run code linters"
	@echo "    make format         Format code with black/ruff"
	@echo "    make version        Show current version"
	@echo "    make dashboard      Open dashboard in browser"
	@echo ""

# ── Setup & Installation ──────────────────────────────────────────────────────
venv:
	@echo "→ Creating virtual environment..."
	python3 -m venv .venv
	$(PYTHON) -m pip install --upgrade pip
	@echo "→ Virtual environment created. Run: source .venv/bin/activate"

install:
	@echo "→ Installing $(PROJECT_NAME)..."
	$(PYTHON) -m pip install -e .

install-dev:
	@echo "→ Installing $(PROJECT_NAME) with dev dependencies..."
	$(PYTHON) -m pip install -e ".[dev]"

env-host:
	@echo "→ Creating sample .env for host..."
	@mkdir -p $(HOME)/.meshpi
	@if [ ! -f $(HOME)/.meshpi/config.env ]; then \
		echo "# MeshPi Host Configuration" > $(HOME)/.meshpi/config.env; \
		echo "HOSTNAME=meshpi-host-1" >> $(HOME)/.meshpi/config.env; \
		echo "WIFI_SSID=YourWiFiNetwork" >> $(HOME)/.meshpi/config.env; \
		echo "WIFI_PASSWORD=YourWiFiPassword" >> $(HOME)/.meshpi/config.env; \
		echo "TIMEZONE=Europe/Warsaw" >> $(HOME)/.meshpi/config.env; \
		echo "LOCALE=en_US.UTF-8" >> $(HOME)/.meshpi/config.env; \
		echo "SSH_PUBLIC_KEY=" >> $(HOME)/.meshpi/config.env; \
		echo "→ Created $(HOME)/.meshpi/config.env"; \
	else \
		echo "→ $(HOME)/.meshpi/config.env already exists"; \
	fi

env-dev:
	@echo "→ Creating .env.example for development..."
	@echo "# MeshPi Development Environment" > .env.example
	@echo "MESHPI_HOST=0.0.0.0" >> .env.example
	@echo "MESHPI_PORT=7422" >> .env.example
	@echo "MESHPI_TEST_HOST=localhost" >> .env.example
	@echo "MESHPI_TEST_PORT=7422" >> .env.example
	@echo "LITELLM_MODEL=gpt-4o" >> .env.example
	@echo "→ Created .env.example"

# ── Testing ───────────────────────────────────────────────────────────────────
test:
	@echo "→ Running unit tests..."
	$(PYTHON) -m pytest tests/ -v --tb=short -q

test-v:
	@echo "→ Running tests with verbose output..."
	$(PYTHON) -m pytest tests/ -v --tb=long

test-cov:
	@echo "→ Running tests with coverage..."
	$(PYTHON) -m pytest tests/ -v --cov=meshpi --cov-report=term-missing --cov-report=html

test-docker:
	@echo "→ Running tests in Docker..."
	$(COMPOSE) run --rm meshpi-test pytest tests/ -v

test-int: up-host
	@echo "→ Running integration tests..."
	@sleep 3
	$(PYTHON) -m pytest tests/ -v -m integration || true
	$(MAKE) down

test-all: test test-docker test-int

# ── Docker Build ──────────────────────────────────────────────────────────────
build:
	@echo "→ Building all Docker images..."
	$(COMPOSE) build --parallel

build-host:
	$(COMPOSE) build meshpi-host

build-client:
	$(COMPOSE) build meshpi-client-1

build-test:
	$(COMPOSE) build meshpi-test

# ── Docker Services ───────────────────────────────────────────────────────────
up:
	@echo "→ Starting host + 2 clients..."
	$(COMPOSE) up -d meshpi-host meshpi-client-1 meshpi-client-2
	@echo ""
	@echo "  Dashboard: http://localhost:7422/dashboard"
	@echo "  API docs:  http://localhost:7422/docs"
	@echo ""

up-host:
	@echo "→ Starting host only..."
	$(COMPOSE) up -d meshpi-host
	@sleep 2
	@curl -s http://localhost:7422/health || echo "  Waiting for host..."
	@echo ""

up-full: up
	@echo "→ Services started. Run 'make logs' to follow logs."

down:
	$(COMPOSE) down

stop:
	$(COMPOSE) stop

restart:
	$(COMPOSE) restart

# ── Logs ─────────────────────────────────────────────────────────────────────
logs:
	$(COMPOSE) logs -f

logs-host:
	$(COMPOSE) logs -f meshpi-host

logs-client:
	$(COMPOSE) logs -f meshpi-client-1

# ── Shell access ──────────────────────────────────────────────────────────────
shell-host:
	$(COMPOSE) exec meshpi-host /bin/bash

shell-client:
	$(COMPOSE) exec meshpi-client-1 /bin/bash

# ── Package & Publish ─────────────────────────────────────────────────────────
wheel:
	@echo "→ Building Python wheel..."
	$(PYTHON) -m build --wheel
	@echo "→ Built: $$(ls dist/*.whl 2>/dev/null || echo 'No wheel found')"

build-dist:
	@echo "→ Building source distribution and wheel..."
	$(PYTHON) -m build
	@ls -la dist/

publish: build-dist
	@echo "→ Publishing to PyPI..."
	@if [ -z "$$PYPI_TOKEN" ]; then \
		echo "Error: PYPI_TOKEN environment variable not set"; \
		exit 1; \
	fi
	$(PYTHON) -m twine upload dist/*
	@echo "→ Published $(PROJECT_NAME) $(VERSION) to PyPI"

publish-test: build-dist
	@echo "→ Publishing to TestPyPI..."
	@if [ -z "$$TEST_PYPI_TOKEN" ]; then \
		echo "Error: TEST_PYPI_TOKEN environment variable not set"; \
		exit 1; \
	fi
	$(PYTHON) -m twine upload dist/* --repository testpypi --username __token__ --password $$TEST_PYPI_TOKEN
	@echo "→ Published $(PROJECT_NAME) $(VERSION) to TestPyPI"

# ── Cleanup ───────────────────────────────────────────────────────────────────
clean: down
	$(COMPOSE) down -v --rmi local 2>/dev/null || true
	docker image rm -f $(IMAGE_HOST) $(IMAGE_CLIENT) $(IMAGE_TEST) 2>/dev/null || true
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	rm -rf dist/ build/ *.egg-info .pytest_cache htmlcov .coverage
	rm -rf meshpi.egg-info/

clean-all: clean
	rm -rf .venv/

clean-volumes:
	$(COMPOSE) down -v

# ── Status ────────────────────────────────────────────────────────────────────
ps:
	$(COMPOSE) ps

status: ps

version:
	@echo "$(PROJECT_NAME) version: $(VERSION)"

# ── Code Quality ──────────────────────────────────────────────────────────────
lint:
	@echo "→ Running linters..."
	$(PYTHON) -m ruff check meshpi/ tests/ || true
	$(PYTHON) -m mypy meshpi/ --ignore-missing-imports || true

format:
	@echo "→ Formatting code..."
	$(PYTHON) -m ruff format meshpi/ tests/

# ── Dashboard ─────────────────────────────────────────────────────────────────
dashboard:
	@echo "→ Opening dashboard..."
	@which xdg-open && xdg-open http://localhost:7422/dashboard || \
	 which open     && open     http://localhost:7422/dashboard || \
	 echo "  Dashboard: http://localhost:7422/dashboard"

# ── CI target (used in GitHub Actions) ────────────────────────────────────────
ci: install-dev test
	@echo "→ CI complete"

# ── Release ───────────────────────────────────────────────────────────────────
release-patch:
	@echo "→ Bumping patch version..."
	@python -c "v='$(VERSION)'.split('.'); v[2]=str(int(v[2])+1); open('VERSION','w').write('.'.join(v))"
	@echo "→ New version: $$(cat VERSION)"

release-minor:
	@echo "→ Bumping minor version..."
	@python -c "v='$(VERSION)'.split('.'); v[1]=str(int(v[1])+1); v[2]='0'; open('VERSION','w').write('.'.join(v))"
	@echo "→ New version: $$(cat VERSION)"

release-major:
	@echo "→ Bumping major version..."
	@python -c "v='$(VERSION)'.split('.'); v[0]=str(int(v[0])+1); v[1]='0'; v[2]='0'; open('VERSION','w').write('.'.join(v))"
	@echo "→ New version: $$(cat VERSION)"

# ── Quick dev commands ────────────────────────────────────────────────────────
dev: install-dev
	@echo "→ Development environment ready"

run-host:
	$(PYTHON) -m meshpi.cli host

run-client:
	$(PYTHON) -m meshpi.cli scan --dry-run

cli:
	$(PYTHON) -m meshpi.cli $(ARGS)