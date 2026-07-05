# cninfo-toolkit

> **Free, open-source Python toolkit for fetching A-share company announcements from [cninfo.com.cn](http://www.cninfo.com.cn/) (巨潮资讯网).**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Type checker: mypy](https://img.shields.io/badge/type%20checker-mypy-blue.svg)](https://mypy-lang.org/)

---

## Why?

The official cninfo.com.cn website hosts **every** A-share company announcement as PDFs. But there's no official Python SDK, and the popular data vendors (Tushare, Wind) lock this data behind paywalls.

**cninfo-toolkit** provides direct access to cninfo's free public API and helps you:

- 📋 **Query announcement metadata** — Get all announcements for any A-share company in the past N days.
- ⬇️ **Download PDFs** — Fetch announcement PDFs with rate limiting and integrity validation.
- 📄 **Extract text & tables** — Parse PDFs into structured JSON for downstream analysis.

All without authentication, without API keys, and without any usage fees.

## Installation

```bash
pip install cninfo-toolkit
```

Or install from source:

```bash
git clone https://github.com/chenliitaz/cninfo-toolkit.git
cd cninfo-toolkit
pip install -e ".[dev]"
```

## Quickstart

### CLI

```bash
# 1. Query announcements
$ cninfo anns 600487.SH 300308.SZ --days 14 --json --output anns.json

# 2. Download PDFs
$ cninfo pdf-dl --anns anns.json --output-dir ./pdfs/

# 3. Extract text and tables
$ cninfo pdf-extract --pdf-dir ./pdfs/ --output-dir ./extracted/

# Or run all 3 steps at once:
$ cninfo pipeline 600487.SH 300308.SZ --days 14 --output-dir ./data/
```

### Python API

```python
from pathlib import Path
from cninfo_toolkit import (
    get_announcements,
    download_pdfs,
    extract_pdfs,
)

# Query announcements
anns = get_announcements("600487.SH", days=14)
print(f"Found {len(anns)} announcements")
for ann in anns[:3]:
    print(f"[{ann.ann_date}] {ann.title}")
    print(f"  URL: {ann.url}")

# Download PDFs
report = download_pdfs(anns, output_dir=Path("./pdfs/"))
print(f"Downloaded {report.success_count}, skipped {report.skipped_count}, failed {report.failed_count}")

# Extract text and tables
pdfs = [Path(r.local_path) for r in report.results if r.success]
extract_report = extract_pdfs(pdfs, output_dir=Path("./extracted/"))
print(f"Extracted {extract_report.success_count} PDFs")
```

### Multi-company batch query

```python
from cninfo_toolkit import batch_query

results = batch_query(
    ["600487.SH", "300308.SZ", "688498.SH"],
    days=14,
)
for ts_code, anns in results.items():
    print(f"{ts_code}: {len(anns)} announcements")
```

## Features

- ✅ **Free** — No API keys, no authentication, no rate-limit fees.
- ✅ **Cross-platform** — Works on macOS, Linux, Windows (Python 3.9+).
- ✅ **Type-safe** — Full type hints with mypy strict mode.
- ✅ **Well-tested** — pytest suite with >70% coverage requirement.
- ✅ **Production-grade** — Rate limiting, retries, PDF integrity validation.
- ✅ **Both CLI and Python API** — Use whichever fits your workflow.
- ✅ **Structured output** — JSON for metadata, text+tables for PDFs.

## Why not just use Tushare / Wind?

These services require:

- 🔒 Paid subscriptions (often thousands of RMB/year)
- 🔒 API tokens with usage caps
- 🔒 Pre-approval for high-volume endpoints

`cninfo-toolkit` bypasses all of this by going **directly to the source** (cninfo's official POST API). The data is the same — it's all public information, just made freely accessible.

## Documentation

Full documentation is available at [chenliitaz.github.io/cninfo-toolkit](https://chenliitaz.github.io/cninfo-toolkit).

- [Installation](docs/installation.md)
- [Quickstart](docs/quickstart.md)
- [API Reference](docs/api.md)
- [Contributing](docs/contributing.md)

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

```bash
# Set up dev environment
git clone https://github.com/chenliitaz/cninfo-toolkit.git
cd cninfo-toolkit
pip install -e ".[dev]"
pre-commit install

# Run tests
pytest

# Run linters
ruff check src tests
ruff format src tests
mypy src/cninfo_toolkit
```

## License

MIT License — see [LICENSE](LICENSE) for details.

## Acknowledgements

- **cninfo.com.cn** (巨潮资讯网) for providing free public access to A-share announcements.
- Inspired by the need to democratize financial data access for individual investors and researchers in China.

## Disclaimer

This toolkit accesses data that is **publicly available** on cninfo.com.cn. It is intended for:

- ✅ Personal research and education
- ✅ Academic studies
- ✅ Building investment analysis tools

It is **not** intended for:

- ❌ Redistribution of cninfo data in commercial products
- ❌ High-volume scraping that violates cninfo's terms of service
- ❌ Any illegal activity

Always respect cninfo's [terms of service](http://www.cninfo.com.cn/new/disclosure) and use this toolkit responsibly. Rate limiting (0.5s/request by default) is enforced to be respectful of cninfo's infrastructure.