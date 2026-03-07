# Contributing to CasConf

Thank you for your interest in contributing to CasConf! Contributions of all kinds are welcome, including bug reports, feature suggestions, documentation improvements, and code changes.

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](https://www.contributor-covenant.org/version/2/1/code_of_conduct/). By participating, you agree to uphold this standard. Please report unacceptable behavior to the project maintainers.

---

## How to Contribute

### Reporting Bugs

1. **Search existing issues** to avoid duplicates.
2. **Open a new issue** with the following information:
   - CasConf version (`casconf --version`)
   - Python version (`python --version`)
   - Operating system
   - Steps to reproduce
   - Expected behavior
   - Actual behavior
   - Relevant configuration files (with sensitive data removed)

### Suggesting Features

1. **Open a new issue** with the label `enhancement`.
2. Describe the use case and why the feature would be valuable.
3. Include a proposed API or CLI interface if relevant.
4. Reference [DESIGN.md](DESIGN.md) if the feature relates to an existing design decision.

### Pull Requests

1. **Fork the repository** and create a branch from `main`:
   ```bash
   git checkout -b feat/my-feature
   ```

2. **Make your changes** following the code style and testing guidelines below.

3. **Run the tests** to ensure nothing is broken:
   ```bash
   pipenv run test
   ```

4. **Run the linters and formatters** to ensure PEP 8 compliance:
   ```bash
   pipenv run lint
   pipenv run format-check
   pipenv run sort-imports-check
   pipenv run typecheck
   ```

5. **Update documentation** if your change affects the public API or CLI interface.

6. **Open a pull request** against `main` with a clear description of the change and the motivation.

---

## Development Setup

### Prerequisites

- Python 3.10 or later
- `git`
- `pipenv` (`pip install pipenv`)

### Setup

```bash
# Clone your fork
git clone https://github.com/<your-username>/casconf.git
cd casconf

# Install all dependencies (including dev) into a managed virtualenv
pipenv install --dev

# Activate the virtual environment
pipenv shell
```

### Project Structure

```
casconf/
├── casconf/            # Source package
│   ├── __init__.py      # Public API re-exports
│   ├── __main__.py      # CLI entry point (python -m casconf)
│   ├── api.py           # Public API implementation
│   ├── cli.py           # CLI argument parsing
│   ├── discovery.py     # Discovery Engine
│   ├── parser.py        # Parser Engine
│   ├── merger.py        # Merger Engine
│   ├── writer.py        # Writer Engine
│   ├── registry.py      # Configuration Registry
│   └── exceptions.py    # Exception hierarchy
├── tests/
│   ├── fixtures/        # Sample configuration files for tests
│   ├── test_cli.py
│   ├── test_coverage.py
│   ├── test_discovery.py
│   ├── test_exceptions.py
│   ├── test_merger.py
│   ├── test_parser.py
│   └── test_writer.py
├── ARCHITECTURE.md
├── API.md
├── CONTRIBUTING.md
├── DESIGN.md
├── LICENSE
├── USAGE.md
├── README.md
├── Pipfile
└── pyproject.toml
```

---

## Running Tests

```bash
# Run all tests
pipenv run test

# Run with coverage report
pipenv run test-cov

# Run a specific test file
pipenv run test tests/test_merger.py

# Run a specific test
pipenv run test tests/test_merger.py::TestDeepMerge::test_merges_nested_dicts

# Run tests matching a keyword
pipenv run test -k "merge"
```

---

## Code Style

CasConf follows **PEP 8 strictly**. The project uses `black` for formatting, `isort` for import ordering, and `flake8` for linting.

### Linting and Formatting

```bash
# Check for linting issues
pipenv run lint

# Auto-format code
pipenv run format

# Check formatting without applying changes
pipenv run format-check

# Sort imports
pipenv run sort-imports

# Check import order without applying changes
pipenv run sort-imports-check
```

### Style Rules

- **Line length**: 127 characters maximum.
- **Imports**: Grouped as stdlib → third-party → local, separated by blank lines.
- **Type hints**: Required for all public functions and methods.
- **Docstrings**: Required for all public modules, classes, and functions.
- **Naming**: `snake_case` for functions and variables, `PascalCase` for classes, `UPPER_CASE` for constants.

### Example: Well-Styled Function

```python
from __future__ import annotations

from pathlib import Path
from typing import Any


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge *override* into *base*, returning a new dict.

    Scalar values in *override* replace those in *base*.
    Dict values are merged recursively.
    List values are concatenated (override appended to base).

    Args:
        base: The base configuration dictionary.
        override: The overriding configuration dictionary.

    Returns:
        A new dict representing the deep-merged result.
    """
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        elif key in result and isinstance(result[key], list) and isinstance(value, list):
            result[key] = result[key] + value
        else:
            result[key] = value
    return result
```

### Example: Well-Styled Class

```python
class DiscoveryConfig:
    """Configuration for the CasConf discovery engine.

    Attributes:
        directories: Ordered list of directories to scan.
        patterns: File name patterns to match within each directory.
        merge_strategy: Merge strategy to use ('deep' or 'shallow').
    """

    def __init__(
        self,
        directories: list[str | Path],
        patterns: list[str],
        merge_strategy: str = "deep",
    ) -> None:
        self.directories = [Path(d) for d in directories]
        self.patterns = patterns
        self.merge_strategy = merge_strategy
```

---

## Testing Guidelines

- **Every public function must have tests.**
- **Every bug fix must include a regression test.**
- **Tests must be deterministic** (no random data without a fixed seed, no time-dependent behavior without mocking).
- **Tests must be independent** (no shared mutable state between tests).
- **Use fixtures** in `tests/fixtures/` for configuration files; do not create temporary files in test functions unless necessary.

### Example Test

```python
import pytest
from casconf.merger import deep_merge


def test_deep_merge_nested_dicts():
    base = {"database": {"host": "localhost", "port": 5432}}
    override = {"database": {"port": 5433, "name": "mydb"}}

    result = deep_merge(base, override)

    assert result == {
        "database": {
            "host": "localhost",
            "port": 5433,
            "name": "mydb",
        }
    }


def test_deep_merge_does_not_mutate_inputs():
    base = {"key": "base_value"}
    override = {"key": "override_value"}

    deep_merge(base, override)

    assert base["key"] == "base_value"
    assert override["key"] == "override_value"


def test_deep_merge_appends_lists():
    base = {"plugins": ["auth", "cache"]}
    override = {"plugins": ["metrics"]}

    result = deep_merge(base, override)

    assert result["plugins"] == ["auth", "cache", "metrics"]
```

---

## Documentation Guidelines

- **Update `API.md`** when adding or changing public API functions, classes, or exceptions.
- **Update `USAGE.md`** when adding features that affect common usage patterns.
- **Update `ARCHITECTURE.md`** when changing system components or data flow.
- **Update `DESIGN.md`** when making significant design decisions that involve trade-offs.
- **Add docstrings** to all public modules, classes, and functions as described in the code style section.

---

## Commit Message Format

CasConf uses [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <short description>

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Formatting, no logic change
- `refactor`: Code change that is neither a feature nor a bug fix
- `test`: Adding or updating tests
- `chore`: Build process, dependency updates, tooling

**Examples:**

```
feat(merger): add support for list replace directive

fix(discovery): handle symlinks in directory scan

docs(api): document output_format parameter for merge_configs

test(merger): add regression test for type conflict warning
```

---

## Release Process

Releases are managed by the project maintainers. The process is:

1. Update `CHANGELOG.md` with changes since the last release.
2. Bump the version in `pyproject.toml`.
3. Tag the commit: `git tag v<version>`.
4. Push the tag: `git push origin v<version>`.
5. The CI pipeline publishes to PyPI automatically.
