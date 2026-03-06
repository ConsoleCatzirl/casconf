# Contributing to CascConf

Thank you for your interest in contributing to CascConf! This document explains how to get involved.

## Code of Conduct

Be kind, respectful, and constructive. We follow the [Contributor Covenant](https://www.contributor-covenant.org/).

## How to Contribute

### Reporting Bugs

Open an issue with:
- A clear title and description.
- Steps to reproduce the issue.
- Expected vs. actual behavior.
- Your Python version and operating system.

### Suggesting Features

Open an issue tagged `enhancement`. Describe the motivation, the proposed behavior, and any relevant examples.

### Submitting a Pull Request

1. **Fork** the repository and create your branch from `main`.
2. **Install dev dependencies:**
   ```bash
   pip install -e ".[dev]"
   ```
3. **Make your changes.** Follow the code style guidelines below.
4. **Write tests** for your changes in the `tests/` directory.
5. **Run the test suite:**
   ```bash
   pytest
   ```
6. **Run the linter:**
   ```bash
   ruff check .
   ```
7. **Open a pull request** against the `main` branch. Fill in the PR template.

## Code Style

- Follow [PEP 8](https://peps.python.org/pep-0008/).
- Use [ruff](https://github.com/astral-sh/ruff) for linting.
- Use type hints for all public functions and methods.
- Keep functions small and focused.
- Prefer the standard library over third-party dependencies where practical.

## License

By contributing, you agree that your contributions will be licensed under the [GNU Affero General Public License v3.0](LICENSE).
