# Installation

## Requirements

- **Python 3.9+** (3.9, 3.10, 3.11, 3.12, 3.13 supported)
- **pip** (or any PEP 517 compatible package manager like `uv`, `poetry`, `pdm`)

## Standard Installation

```bash
pip install cninfo-toolkit
```

That's it! The `cninfo` command is now available globally.

## Verify Installation

```bash
# Check the installed version
$ cninfo --version
cninfo-toolkit 0.1.0

# Show help
$ cninfo --help
```

## Optional: Install with `uv` (faster)

[uv](https://github.com/astral-sh/uv) is a fast Python package manager written in Rust.

```bash
# Install uv (if you haven't)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install cninfo-toolkit
uv pip install cninfo-toolkit

# Or use uvx to run without installing
uvx cninfo anns 600487.SH
```

## Optional: Development Installation

To install from source for development:

```bash
git clone https://github.com/chenliitaz/cninfo-toolkit.git
cd cninfo-toolkit

# Using pip
pip install -e ".[dev]"

# Or using uv
uv pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

The `[dev]` extra installs:

- `pytest`, `pytest-cov`, `pytest-mock` — for testing
- `ruff` — for linting and formatting
- `mypy`, `types-requests` — for type checking
- `pre-commit` — for git hooks
- `mkdocs`, `mkdocs-material` — for documentation

## Docker (Optional)

Build a Docker image:

```dockerfile
FROM python:3.12-slim
RUN pip install cninfo-toolkit
ENTRYPOINT ["cninfo"]
```

Build and run:

```bash
docker build -t cninfo-toolkit .
docker run --rm cninfo-toolkit anns 600487.SH --days 7
```

## Troubleshooting

### `command not found: cninfo`

The `cninfo` CLI is installed in your Python environment's `bin/` directory. Make
sure your environment's `bin/` is in your `PATH`.

```bash
# If using venv
source .venv/bin/activate

# If using conda
conda activate myenv

# Check where cninfo was installed
pip show cninfo-toolkit
# Look at "Location" and check the bin/ subdirectory
```

### `ModuleNotFoundError: No module named 'cninfo_toolkit'`

Your Python interpreter might be different from the one used to install. Check:

```bash
which python
which pip
python -c "import sys; print(sys.executable)"
```

Make sure they all point to the same environment.

### `requests.exceptions.ConnectionError`

cninfo-toolkit needs network access to:

- `http://www.cninfo.com.cn/new/hisAnnouncement/query`
- `http://www.cninfo.com.cn/new/data/szse_stock.json`
- `http://static.cninfo.com.cn/finalpage/...PDF`

Check your firewall / proxy settings.

### PDF extraction is slow

This is normal. PDF extraction with `pdfplumber` is CPU-bound. To speed it up:

- Process fewer PDFs at a time
- Lower `--max-pages` for large PDFs
- Use a machine with more CPUs

## Next steps

- [Quickstart](quickstart.md) — See practical examples
- [API Reference](api.md) — Complete API documentation