SHELL := /bin/bash

# ─────────────────────────────────────────────────────────────────────────────
# MeshPi Makefile
# ─────────────────────────────────────────────────────────────────────────────

# Define colors for better output
GREEN  := $(shell tput -Txterm setaf 2 2>/dev/null || echo "")
YELLOW := $(shell tput -Txterm setaf 3 2>/dev/null || echo "")
WHITE  := $(shell tput -Txterm setaf 7 2>/dev/null || echo "")
CYAN   := $(shell tput -Txterm setaf 6 2>/dev/null || echo "")
RESET  := $(shell tput -Txterm sgr0 2>/dev/null || echo "")

# Project information
PACKAGE := meshpi
VERSION := $(shell cat VERSION 2>/dev/null || echo "0.1.6")
PYTHON  := .venv/bin/python
PIP     := .venv/bin/pip
PYTEST  := .venv/bin/pytest
PART    := patch

# Docker
COMPOSE      := docker compose
IMAGE_HOST   := meshpi-host:latest
IMAGE_CLIENT := meshpi-client:latest

.PHONY: help install dev test build publish clean push venv env-host

# ── Help ──────────────────────────────────────────────────────────────────────
help:
	@echo ""
	@echo "  $(CYAN)MeshPi — Development & Deployment Commands$(RESET)"
	@echo "  ──────────────────────────────────────────────────────────"
	@echo ""
	@echo "  $(WHITE)Setup & Installation:$(RESET)"
	@echo "    make venv           Create virtual environment"
	@echo "    make install        Install package locally"
	@echo "    make dev            Install in development mode"
	@echo "    make env-host       Create sample config for host"
	@echo ""
	@echo "  $(WHITE)Testing:$(RESET)"
	@echo "    make test           Run tests"
	@echo "    make test-v         Run tests with verbose output"
	@echo "    make test-cov       Run tests with coverage"
	@echo ""
	@echo "  $(WHITE)Package & Publish:$(RESET)"
	@echo "    make build          Build package for PyPI"
	@echo "    make publish        Build and upload to PyPI"
	@echo "    make bump-version   Bump version (PART=patch|minor|major)"
	@echo ""
	@echo "  $(WHITE)Docker:$(RESET)"
	@echo "    make docker-build   Build Docker images"
	@echo "    make docker-up      Start services"
	@echo "    make docker-down    Stop services"
	@echo ""
	@echo "  $(WHITE)Utilities:$(RESET)"
	@echo "    make clean          Remove build artifacts"
	@echo "    make push           Use goal to push changes"
	@echo "    make version        Show current version"
	@echo ""

# ── Setup & Installation ──────────────────────────────────────────────────────
venv:
	@echo "$(YELLOW)→ Creating virtual environment...$(RESET)"
	python3 -m venv .venv
	$(PIP) install --upgrade pip
	@echo "$(GREEN)✓ Virtual environment created$(RESET)"
	@echo "  Run: source .venv/bin/activate"

install:
	@echo "$(YELLOW)→ Installing $(PACKAGE)...$(RESET)"
	$(PIP) install .
	@echo "$(GREEN)✓ Installed $(PACKAGE)$(RESET)"

dev:
	@echo "$(YELLOW)→ Installing $(PACKAGE) in development mode...$(RESET)"
	$(PIP) install -e ".[dev]"
	@echo "$(GREEN)✓ Development environment ready$(RESET)"

env-host:
	@echo "$(YELLOW)→ Creating sample config for host...$(RESET)"
	@mkdir -p $(HOME)/.meshpi
	@if [ ! -f $(HOME)/.meshpi/config.env ]; then \
		echo "# MeshPi Host Configuration" > $(HOME)/.meshpi/config.env; \
		echo "HOSTNAME=meshpi-host-1" >> $(HOME)/.meshpi/config.env; \
		echo "WIFI_SSID=YourWiFiNetwork" >> $(HOME)/.meshpi/config.env; \
		echo "WIFI_PASSWORD=YourWiFiPassword" >> $(HOME)/.meshpi/config.env; \
		echo "TIMEZONE=Europe/Warsaw" >> $(HOME)/.meshpi/config.env; \
		echo "LOCALE=en_US.UTF-8" >> $(HOME)/.meshpi/config.env; \
		echo "$(GREEN)✓ Created $(HOME)/.meshpi/config.env$(RESET)"; \
	else \
		echo "$(YELLOW)→ $(HOME)/.meshpi/config.env already exists$(RESET)"; \
	fi

# ── Testing ───────────────────────────────────────────────────────────────────
test:
	@echo "$(YELLOW)→ Running tests...$(RESET)"
	$(PYTEST) tests/ -q --tb=short

test-v:
	@echo "$(YELLOW)→ Running tests with verbose output...$(RESET)"
	$(PYTEST) tests/ -v --tb=short

test-cov:
	@echo "$(YELLOW)→ Running tests with coverage...$(RESET)"
	$(PYTEST) tests/ -v --cov=$(PACKAGE) --cov-report=term-missing

# ── Package & Publish ─────────────────────────────────────────────────────────
build: clean
	@echo "$(YELLOW)→ Building package for PyPI...$(RESET)"
	$(PIP) install --upgrade build twine
	$(PYTHON) -m build --sdist --wheel
	@echo "$(GREEN)✓ Built: $(shell ls dist/*.whl 2>/dev/null)$(RESET)"

publish: bump-version build
	@echo "$(YELLOW)→ Uploading to PyPI...$(RESET)"
	@if [ -z "$$PYPI_TOKEN" ]; then \
		echo "$(YELLOW)Error: PYPI_TOKEN environment variable not set$(RESET)"; \
		exit 1; \
	fi
	$(PYTHON) -m twine upload dist/* --username __token__ --password $$PYPI_TOKEN
	@echo "$(GREEN)✓ Published $(PACKAGE) $(VERSION) to PyPI$(RESET)"

publish-test: build
	@echo "$(YELLOW)→ Uploading to TestPyPI...$(RESET)"
	@if [ -z "$$TEST_PYPI_TOKEN" ]; then \
		echo "$(YELLOW)Error: TEST_PYPI_TOKEN environment variable not set$(RESET)"; \
		exit 1; \
	fi
	$(PYTHON) -m twine upload dist/* --repository testpypi --username __token__ --password $$TEST_PYPI_TOKEN
	@echo "$(GREEN)✓ Published $(PACKAGE) $(VERSION) to TestPyPI$(RESET)"

## Bump version (e.g., make bump-version PART=patch)
bump-version:
	@if [ -z "$(PART)" ]; then \
		echo "$(YELLOW)Error: PART variable not set. Usage: make bump-version PART=<major|minor|patch>$(RESET)"; \
		exit 1; \
	fi
	@echo "$(YELLOW)Bumping $(PART) version...$(RESET)"
	@CURRENT=$$(cat VERSION); \
	IFS='.' read -r MAJOR MINOR PATCH <<< "$$CURRENT"; \
	case "$(PART)" in \
		major) MAJOR=$$((MAJOR + 1)); MINOR=0; PATCH=0 ;; \
		minor) MINOR=$$((MINOR + 1)); PATCH=0 ;; \
		patch) PATCH=$$((PATCH + 1)) ;; \
	esac; \
	NEW_VERSION="$$MAJOR.$$MINOR.$$PATCH"; \
	echo "$$NEW_VERSION" > VERSION; \
	sed -i "s/version = \".*\"/version = \"$$NEW_VERSION\"/" pyproject.toml; \
	sed -i "s/__version__ = \".*\"/__version__ = \"$$NEW_VERSION\"/" meshpi/__init__.py; \
	git add VERSION pyproject.toml meshpi/__init__.py; \
	git commit -m "Bump version to $$NEW_VERSION"; \
	if git rev-parse "v$$NEW_VERSION" >/dev/null 2>&1; then \
		echo "$(YELLOW)Error: tag 'v$$NEW_VERSION' already exists$(RESET)"; \
		exit 1; \
	fi; \
	git tag -a "v$$NEW_VERSION" -m "Version $$NEW_VERSION"; \
	echo "$(GREEN)✓ Version bumped to $$NEW_VERSION$(RESET)"

# ── Docker ────────────────────────────────────────────────────────────────────
docker-build:
	@echo "$(YELLOW)→ Building Docker images...$(RESET)"
	$(COMPOSE) build --parallel
	@echo "$(GREEN)✓ Docker images built$(RESET)"

docker-up:
	@echo "$(YELLOW)→ Starting services...$(RESET)"
	$(COMPOSE) up -d meshpi-host
	@sleep 2
	@curl -s http://localhost:7422/health && echo "" || true
	@echo "$(GREEN)✓ Services started$(RESET)"
	@echo "  Dashboard: http://localhost:7422/dashboard"
	@echo "  API docs:  http://localhost:7422/docs"

docker-down:
	@echo "$(YELLOW)→ Stopping services...$(RESET)"
	$(COMPOSE) down
	@echo "$(GREEN)✓ Services stopped$(RESET)"

docker-logs:
	$(COMPOSE) logs -f

# ── Cleanup ───────────────────────────────────────────────────────────────────
clean:
	@echo "$(YELLOW)→ Cleaning build artifacts...$(RESET)"
	rm -rf dist build *.egg-info .pytest_cache htmlcov .coverage
	rm -rf $(PACKAGE).egg-info/
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)✓ Cleaned$(RESET)"

clean-all: clean
	rm -rf .venv/

# ── Utilities ─────────────────────────────────────────────────────────────────
push: bump-version
	@echo "$(YELLOW)→ Pushing changes...$(RESET)"
	@if command -v goal &> /dev/null; then \
		goal push; \
	else \
		echo "$(YELLOW)Goal not installed. Run 'make install' first.$(RESET)"; \
	fi

version:
	@echo "$(PACKAGE) version: $(VERSION)"

lint:
	@echo "$(YELLOW)→ Running linters...$(RESET)"
	$(PYTHON) -m ruff check $(PACKAGE)/ tests/ || true

format:
	@echo "$(YELLOW)→ Formatting code...$(RESET)"
	$(PYTHON) -m ruff format $(PACKAGE)/ tests/

# ── CI target ─────────────────────────────────────────────────────────────────
ci: dev test
	@echo "$(GREEN)✓ CI complete$(RESET)"