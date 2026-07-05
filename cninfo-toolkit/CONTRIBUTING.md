# Contributing to cninfo-toolkit

First off, thanks for taking the time to contribute! 🎉

The following is a set of guidelines for contributing to cninfo-toolkit. These are mostly guidelines, not rules. Use your best judgment, and feel free to propose changes to this document in a pull request.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Style Guide](#style-guide)
- [Commit Messages](#commit-messages)
- [Pull Request Process](#pull-request-process)

## Code of Conduct

This project and everyone participating in it is governed by the [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to the maintainers.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the [issue tracker](https://github.com/chenliitaz/cninfo-toolkit/issues) to avoid duplicates. When creating a bug report, include:

- A clear, descriptive title
- Steps to reproduce the issue
- Expected vs actual behavior
- Python version, OS, package version
- Any relevant code snippets or error logs

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, include:

- A clear, descriptive title
- A detailed description of the proposed functionality
- Use cases / motivation
- Example API or CLI usage

### Pull Requests

- Fill in the required template
- Follow the [style guide](#style-guide)
- Include tests for new features
- Update documentation (README, docstrings, CHANGELOG)
- End all files with a newline
- Avoid platform-dependent code

## Development Setup

### Prerequisites

- Python 3.9 or higher
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- Git

### Setup with uv (recommended)

```bash
# Clone the repo
git clone https://github.com/chenliitaz/cninfo-toolkit.git
cd cninfo-toolkit

# Create virtual environment and install deps
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Setup with pip

```bash
git clone https://github.com/chenliitaz/cninfo-toolkit.git
cd cninfo-toolkit
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=cninfo_toolkit --cov-report=term-missing

# Run specific test file
pytest tests/test_anns.py

# Run specific test
pytest tests/test_anns.py::TestGetAnnouncements::test_returns_announcements
```

### Linting & Type Checking

```bash
# Auto-fix lint issues
ruff check --fix src tests
ruff format src tests

# Type checking
mypy src/cninfo_toolkit

# Run all pre-commit hooks
pre-commit run --all-files
```

### Building Documentation

```bash
# Serve docs locally
mkdocs serve

# Build static docs
mkdocs build
```

## Style Guide

### Python Style

- We use [Ruff](https://github.com/astral-sh/ruff) for linting and formatting (configured in `pyproject.toml`).
- Line length: 100 characters max.
- Use type hints for all function signatures.
- Use docstrings (Google-style) for all public functions and classes.
- Prefer `pathlib.Path` over `os.path`.
- Prefer f-strings over `.format()` or `%` formatting.

### Module Organization

```
src/cninfo_toolkit/
├── __init__.py        # Public API surface
├── _cli.py            # Typer CLI (private, exposed via entry point)
├── _utils.py          # Shared utilities (private)
├── anns.py            # Announcement metadata
├── pdf_dl.py          # PDF download
└── pdf_extract.py     # PDF extraction
```

- Public API goes in `__init__.py`.
- Internal modules start with `_` (e.g., `_cli`, `_utils`).

### Testing

- Write tests for all new features.
- Aim for >80% coverage on new code (project requires >70% overall).
- Use `pytest` fixtures (defined in `tests/conftest.py`) for shared setup.
- Mock external HTTP calls using `unittest.mock.patch`.
- Test edge cases: empty inputs, invalid codes, network failures.

### Documentation

- Update README.md for user-facing changes.
- Update docstrings for API changes.
- Add an entry to CHANGELOG.md under "Unreleased".
- Add examples to `examples/` for new use cases.

## Commit Messages

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style (formatting, no logic change)
- `refactor`: Code change that neither fixes a bug nor adds a feature
- `perf`: Performance improvement
- `test`: Adding or fixing tests
- `chore`: Build process or auxiliary tool changes

Examples:
```
feat(anns): add support for custom date ranges
fix(pdf-dl): handle redirects correctly
docs: update installation instructions
```

## Pull Request Process

1. **Fork** the repo and create your branch from `main`:
   ```bash
   git checkout -b feat/your-feature-name
   ```

2. **Make your changes** following the style guide.

3. **Add tests** for new features.

4. **Update documentation** (README, docstrings, CHANGELOG).

5. **Verify** all checks pass:
   ```bash
   pytest
   ruff check src tests
   ruff format --check src tests
   mypy src/cninfo_toolkit
   ```

6. **Commit** with a Conventional Commits message.

7. **Push** your branch and open a Pull Request.

8. **Wait for review.** A maintainer will review your PR and may request changes.

9. **Merge:** Once approved, a maintainer will merge your PR.

## Release Process

Releases are managed by maintainers via GitHub Releases and PyPI.

1. Update version in `pyproject.toml` and `src/cninfo_toolkit/__init__.py`
2. Update `CHANGELOG.md` with the release date
3. Tag the commit: `git tag -a v0.X.Y -m "Release v0.X.Y"`
4. Push tag: `git push origin v0.X.Y`
5. Build and upload to PyPI:
   ```bash
   python -m build
   twine upload dist/*
   ```
6. Create GitHub Release with auto-generated notes

## Questions?

Feel free to open an issue with the "question" label, or reach out to the maintainers.

Thanks for contributing! 💪