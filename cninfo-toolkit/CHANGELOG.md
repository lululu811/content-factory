# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-07-05

### Added

- Initial public release.
- **`cninfo anns` CLI command** — Query A-share announcement metadata via cninfo's free POST API.
- **`cninfo pdf-dl` CLI command** — Download announcement PDFs with rate limiting and integrity validation.
- **`cninfo pdf-extract` CLI command** — Extract text and tables from PDFs using pdfplumber.
- **`cninfo pipeline` CLI command** — Run all three steps in sequence.
- Python API:
  - `cninfo_toolkit.get_announcements(ts_code, days)` — Query single company.
  - `cninfo_toolkit.batch_query(ts_codes, days)` — Query multiple companies.
  - `cninfo_toolkit.download_pdfs(anns, output_dir)` — Batch download with reports.
  - `cninfo_toolkit.extract_pdfs(pdfs, output_dir)` — Batch extract with reports.
  - `cninfo_toolkit.format_markdown_summary(results)` — Human-readable summaries.
- Cross-platform support (macOS, Linux, Windows).
- Full type hints with mypy strict mode.
- Pytest test suite with >70% coverage requirement.
- Pre-commit hooks (ruff + mypy).
- GitHub Actions CI (lint + test matrix).
- MkDocs Material documentation.
- Examples directory with end-to-end usage.

### Notes

- This package supersedes the standalone scripts in content-factory (`scripts/cninfo-*.py`).
- The `bin/cninfo-pipeline.sh` wrapper in content-factory is updated to call the new CLI.

[Unreleased]: https://github.com/chenliitaz/cninfo-toolkit/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/chenliitaz/cninfo-toolkit/releases/tag/v0.1.0