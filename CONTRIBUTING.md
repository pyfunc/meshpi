# Contributing to MeshPi

Thank you for your interest in contributing to MeshPi! This document provides guidelines and instructions for contributing.

## Development Setup

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- git
- Make (optional, for convenience commands)

### Getting Started

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/meshpi.git
   cd meshpi
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install development dependencies**
   ```bash
   pip install -e ".[dev]"
   ```

4. **Run tests to verify setup**
   ```bash
   make test
   # or
   pytest tests/ -v
   ```

## Development Workflow

### Running Tests

```bash
# Run all tests
make test

# Run with coverage
make coverage

# Run specific test file
pytest tests/test_meshpi.py -v

# Run specific test
pytest tests/test_meshpi.py::test_parse_target -v
```

### Code Style

MeshPi uses [ruff](https://github.com/astral-sh/ruff) for linting and formatting:

```bash
# Check for issues
make lint

# Auto-fix issues
ruff check --fix meshpi/
ruff format meshpi/
```

### Type Checking

We use mypy for static type checking:

```bash
mypy meshpi/
```

## Pull Request Process

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write clean, documented code
   - Add tests for new functionality
   - Update documentation as needed

3. **Run tests and linting**
   ```bash
   make test
   make lint
   ```

4. **Commit your changes**
   ```bash
   git commit -m "feat: description of your change"
   ```

   We follow [Conventional Commits](https://www.conventionalcommits.org/):
   - `feat:` - New features
   - `fix:` - Bug fixes
   - `docs:` - Documentation changes
   - `test:` - Test additions/changes
   - `refactor:` - Code refactoring
   - `chore:` - Maintenance tasks

5. **Push and create a PR**
   ```bash
   git push origin feature/your-feature-name
   ```

   Then create a Pull Request on GitHub.

## Code Guidelines

### General Principles

- **Keep it simple** - Write clear, readable code
- **Document public APIs** - Use docstrings for all public modules, classes, and functions
- **Write tests** - Aim for good test coverage of new functionality
- **Handle errors gracefully** - Provide helpful error messages

### Python Style

- Follow [PEP 8](https://peps.python.org/pep-0008/) conventions
- Use type hints for function signatures
- Use f-strings for string formatting
- Use context managers for resource handling

### Example

```python
from __future__ import annotations
from typing import Optional

def parse_target(target: str) -> tuple[str, str, int]:
    """
    Parse a target string into user, host, and port components.
    
    Args:
        target: Target string like 'user@host:port' or 'host'
    
    Returns:
        Tuple of (user, host, port)
    
    Raises:
        ValueError: If target format is invalid
    """
    # Implementation here
    pass
```

## Adding Hardware Profiles

Hardware profiles are defined in `meshpi/hardware/profiles.py`. To add a new profile:

1. Create a `HardwareProfile` instance with required fields:
   - `id`: Unique identifier (e.g., `oled_ssd1306_i2c`)
   - `name`: Human-readable name
   - `category`: One of the defined categories
   - `description`: Brief description
   - `packages`: List of apt packages to install
   - `overlays`: Device tree overlays
   - `post_commands`: Shell commands to run after installation

2. Add tests for the new profile in `tests/test_meshpi.py`

## Reporting Issues

### Bug Reports

When reporting bugs, please include:

1. MeshPi version (`meshpi --version`)
2. Python version (`python --version`)
3. Operating system
4. Steps to reproduce
5. Expected behavior
6. Actual behavior
7. Relevant logs (use `meshpi diag` to collect)

### Feature Requests

For feature requests, please describe:

1. The problem you're trying to solve
2. Your proposed solution
3. Any alternative solutions you've considered
4. Any additional context

## Release Process

Maintainers follow these steps for releases:

1. Update `VERSION` file
2. Update `CHANGELOG.md`
3. Create git tag: `git tag v1.x.x`
4. Push tag: `git push --tags`
5. GitHub Actions will build and publish to PyPI

## Getting Help

- **GitHub Issues**: For bug reports and feature requests
- **GitHub Discussions**: For questions and general discussion
- **Email**: tom@sapletta.com

## License

By contributing to MeshPi, you agree that your contributions will be licensed under the Apache License 2.0.

---

Thank you for contributing to MeshPi! 🎉