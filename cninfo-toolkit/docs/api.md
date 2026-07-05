# API Reference

Complete reference for the public Python API of cninfo-toolkit.

## Module: `cninfo_toolkit`

### High-level functions

#### `get_announcements(ts_code, days=14, *, start_date=None, end_date=None, page_size=30)`

Query announcements for a single company.

**Parameters:**

- `ts_code` (str): TS-format stock code (e.g., `"600487.SH"`).
- `days` (int): Number of days to look back (default `14`). Ignored if `start_date` is given.
- `start_date` (str | None): Start date in `YYYY-MM-DD` format (overrides `days`).
- `end_date` (str | None): End date in `YYYY-MM-DD` format (default: today).
- `page_size` (int): Max announcements to fetch (default `30`).

**Returns:** `list[Announcement]`

**Raises:** `ValueError` if `ts_code` is not in valid TS format.

**Example:**

```python
from cninfo_toolkit import get_announcements

anns = get_announcements("600487.SH", days=14)
for ann in anns:
    print(f"[{ann.ann_date}] {ann.title}")
```

---

#### `batch_query(ts_codes, days=14, *, rate_limit=0.5)`

Query announcements for multiple companies.

**Parameters:**

- `ts_codes` (list[str]): List of TS-format stock codes.
- `days` (int): Number of days to look back (default `14`).
- `rate_limit` (float): Seconds to sleep between requests (default `0.5`).

**Returns:** `dict[str, list[Announcement]]` (mapping `ts_code` → announcements)

**Example:**

```python
from cninfo_toolkit import batch_query

results = batch_query(
    ["600487.SH", "300308.SZ", "688498.SH"],
    days=14,
)
for ts_code, anns in results.items():
    print(f"{ts_code}: {len(anns)} announcements")
```

---

#### `download_pdfs(anns, output_dir, *, skip_existing=True, rate_limit=0.5, timeout=30, retries=3, max_downloads=0)`

Download a batch of announcement PDFs.

**Parameters:**

- `anns` (list[Announcement]): List of announcements to download.
- `output_dir` (Path): Base output directory (created if needed).
- `skip_existing` (bool): If True, skip files that already exist and are valid (default `True`).
- `rate_limit` (float): Seconds to sleep between downloads (default `0.5`).
- `timeout` (int): HTTP timeout per attempt in seconds (default `30`).
- `retries` (int): Number of retries per file (default `3`).
- `max_downloads` (int): If >0, stop after this many downloads (default `0` = unlimited).

**Returns:** `BatchDownloadReport`

**Example:**

```python
from pathlib import Path
from cninfo_toolkit import get_announcements, download_pdfs

anns = get_announcements("600487.SH", days=14)
report = download_pdfs(anns, output_dir=Path("./pdfs/"))
print(f"Downloaded: {report.success_count}")
print(f"Failed: {report.failed_count}")
```

---

#### `extract_pdfs(pdfs, output_dir, *, skip_existing=True, max_pages=30, size_threshold_kb=100, rate_limit=0.3)`

Extract text and tables from a batch of PDFs.

**Parameters:**

- `pdfs` (list[Path]): List of PDF paths.
- `output_dir` (Path): Where to write extracted JSON files (created if needed).
- `skip_existing` (bool): If True, skip files that already have a valid JSON output (default `True`).
- `max_pages` (int): Maximum pages to extract per PDF when large (default `30`).
- `size_threshold_kb` (int): File size threshold (KB) above which `max_pages` is enforced (default `100`).
- `rate_limit` (float): Seconds to sleep between extractions (default `0.3`).

**Returns:** `BatchExtractionReport`

**Example:**

```python
from pathlib import Path
from cninfo_toolkit import extract_pdfs

pdfs = list(Path("./pdfs/").glob("*.PDF"))
report = extract_pdfs(pdfs, output_dir=Path("./extracted/"))
print(f"Extracted: {report.success_count}")
```

---

#### `format_markdown_summary(results, *, title="公告摘要")`

Format batch results as a Markdown summary.

**Parameters:**

- `results` (dict[str, list[Announcement]]): Results from `batch_query` or single-company results.
- `title` (str): Section title (default `"公告摘要"`).

**Returns:** `str` (Markdown formatted)

**Example:**

```python
from cninfo_toolkit import batch_query, format_markdown_summary

results = batch_query(["600487.SH"])
md = format_markdown_summary(results, title="光纤产业链公告")
print(md)
```

---

## Data models

### `Announcement`

Represents a single announcement from cninfo.

**Fields:**

| Field | Type | Description |
|---|---|---|
| `ann_id` | `str` | The cninfo announcement ID (e.g., `"1225380372"`) |
| `ts_code` | `str` | TS-format stock code (e.g., `"600487.SH"`) |
| `org_id` | `str` | The cninfo internal orgId for the company |
| `ann_date` | `str` | Announcement date in `YYYY-MM-DD` format |
| `title` | `str` | Announcement title |
| `url` | `str` | Full URL to the announcement PDF |
| `sec_code` | `str` | The 6-digit securities code (e.g., `"600487"`) |

**Methods:**

- `to_dict() -> dict[str, str]`: Convert to a dict for JSON serialization.

---

### `DownloadResult`

Represents the result of a single PDF download attempt.

**Fields:**

| Field | Type | Description |
|---|---|---|
| `ann_id` | `str` | Announcement ID (from `Announcement.ann_id`) |
| `ts_code` | `str` | Stock code |
| `ann_date` | `str` | Announcement date |
| `title` | `str` | Announcement title |
| `url` | `str` | Original PDF URL |
| `local_path` | `str` | Local file path (empty if failed) |
| `size_kb` | `int` | Downloaded file size in KB (0 if failed) |
| `skipped` | `bool` | True if the file already existed and was skipped |
| `error` | `str` | Error message (empty on success) |

**Properties:**

- `success: bool` — Whether the download succeeded (or was skipped).

**Methods:**

- `to_dict() -> dict[str, Any]`: Convert to a dict for JSON serialization.

---

### `BatchDownloadReport`

Aggregate report of a batch download.

**Fields:**

| Field | Type | Description |
|---|---|---|
| `success_count` | `int` | Number of successful downloads |
| `skipped_count` | `int` | Number of files skipped (already existed) |
| `failed_count` | `int` | Number of failed downloads |
| `total_count` | `int` | Total download attempts |
| `results` | `list[DownloadResult]` | Individual results |
| `downloaded_at` | `str` | ISO 8601 timestamp of completion |

**Methods:**

- `to_dict() -> dict[str, Any]`: Convert to a dict for JSON serialization.

---

### `ExtractionResult`

Represents the result of extracting a single PDF.

**Fields:**

| Field | Type | Description |
|---|---|---|
| `pdf_path` | `str` | Source PDF path |
| `page_count` | `int` | Total pages in the PDF |
| `pages_processed` | `int` | Pages actually extracted (may be < `page_count` if truncated) |
| `truncated` | `bool` | True if max-pages limit was hit |
| `file_size_kb` | `float` | PDF size in KB |
| `full_text` | `str` | Extracted text with `=== Page N ===` headers |
| `tables` | `list[dict]` | Extracted tables (each: `{"page": int, "rows": list[list[str]]}`) |
| `table_count` | `int` | Number of extracted tables |
| `error` | `str` | Error message (empty on success) |

**Properties:**

- `success: bool` — Whether extraction succeeded.

**Methods:**

- `to_dict() -> dict[str, Any]`: Convert to a dict for JSON serialization.

---

### `BatchExtractionReport`

Aggregate report of a batch extraction.

**Fields:**

| Field | Type | Description |
|---|---|---|
| `success_count` | `int` | Number of successful extractions |
| `skipped_count` | `int` | Number of files skipped (already extracted) |
| `failed_count` | `int` | Number of failed extractions |
| `total_count` | `int` | Total extraction attempts |
| `results` | `list[ExtractionResult]` | Individual results |
| `extracted_at` | `str` | ISO 8601 timestamp of completion |

**Methods:**

- `to_dict() -> dict[str, Any]`: Convert to a dict for JSON serialization.

---

## Utility functions

### `is_valid_ts_code(code: str) -> bool`

Check if a string is a valid TS-format stock code.

**Example:**

```python
from cninfo_toolkit import is_valid_ts_code

is_valid_ts_code("600487.SH")  # True
is_valid_ts_code("600487")     # False
is_valid_ts_code("600487.sh")  # False
```

---

### `parse_ts_code_list(text: str) -> list[str]`

Parse a text blob for valid TS-format stock codes.

**Example:**

```python
from cninfo_toolkit import parse_ts_code_list

text = "600487.SH, 300308.SZ; 000070.SZ\n688498.SH"
codes = parse_ts_code_list(text)
# ['600487.SH', '300308.SZ', '000070.SZ', '688498.SH']
```

---

### `sanitize_filename(title: str, max_length: int = 50) -> str`

Sanitize a title into a safe filename slug.

**Example:**

```python
from cninfo_toolkit import sanitize_filename

sanitize_filename("关于 2024 年报的问询函")  # '关于 2024 年报的问询函'
sanitize_filename("foo/bar:baz*qux", max_length=10)  # 'foo-bar-ba'
```

---

## CLI Reference

### `cninfo --version`

Show the version and exit.

### `cninfo anns [TS_CODES...] [OPTIONS]`

Query announcement metadata.

**Arguments:**

- `TS_CODES...` — TS-format stock codes (space-separated).

**Options:**

- `--code-file PATH` — Read stock codes from a file.
- `--code-stdin` — Read stock codes from stdin.
- `--days, -d INT` — Number of days to look back (default: `14`).
- `--start TEXT` — Start date in `YYYY-MM-DD` format.
- `--end TEXT` — End date in `YYYY-MM-DD` format (default: today).
- `--json` — Output JSON instead of Markdown.
- `--output, -o PATH` — Write to file (default: stdout).

### `cninfo pdf-dl [OPTIONS]`

Download announcement PDFs.

**Options:**

- `--anns PATH` — Announcements JSON file (output of `cninfo anns --json`).
- `--url TEXT` — Download a single PDF URL (mutually exclusive with `--anns`).
- `--output, -o PATH` — Output path for single URL mode.
- `--output-dir PATH` — Output directory for batch mode (default: `./pdfs`).
- `--skip-existing / --no-skip-existing` — Skip existing files (default: skip).
- `--max INT` — Max downloads (default: `0` = unlimited).
- `--rate-limit FLOAT` — Seconds between requests (default: `0.5`).
- `--retries INT` — Retries per file (default: `3`).

### `cninfo pdf-extract [OPTIONS]`

Extract text and tables from announcement PDFs.

**Options:**

- `--pdf PATH` — Extract a single PDF.
- `--pdf-dir PATH` — Extract all PDFs in a directory.
- `--manifest PATH` — Use `manifest.json` from `cninfo pdf-dl`.
- `--output-dir PATH` — Output directory for JSON files (default: `./extracted`).
- `--skip-existing / --no-skip-existing` — Skip existing files (default: skip).
- `--max-pages INT` — Maximum pages per PDF (default: `30`).
- `--size-threshold-kb INT` — Threshold for triggering max-pages (default: `100`).

### `cninfo pipeline [TS_CODES...] [OPTIONS]`

Run the full pipeline: query → download → extract.

**Arguments:**

- `TS_CODES...` — TS-format stock codes.

**Options:**

- `--code-file PATH` — Read stock codes from a file.
- `--code-stdin` — Read stock codes from stdin.
- `--days, -d INT` — Number of days to look back (default: `14`).
- `--output-dir PATH` — Base output directory (default: `./cninfo-output`).