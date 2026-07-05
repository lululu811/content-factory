"""cninfo-toolkit: A free Python toolkit for cninfo.com.cn (巨潮资讯网) announcements.

This package provides three core capabilities:

1. **Announcements metadata** — Query A-share company announcements via the
   cninfo official API (bypasses the Tushare paid wall).

2. **PDF download** — Download announcement PDFs with rate limiting, retries,
   and integrity validation.

3. **PDF extraction** — Extract text and tables from PDFs using pdfplumber.

Both CLI and Python API are supported.

Quickstart (CLI):
    $ pip install cninfo-toolkit
    $ cninfo anns 600487.SH --days 14 --json --output anns.json
    $ cninfo pdf-dl --anns anns.json --output-dir ./pdfs/
    $ cninfo pdf-extract --manifest ./pdfs/manifest.json --output-dir ./extracted/

Quickstart (Python API):
    >>> from cninfo_toolkit import get_announcements, download_pdfs, extract_pdfs
    >>> anns = get_announcements("600487.SH", days=14)
    >>> pdfs = download_pdfs(anns, output_dir="./pdfs/")
    >>> extracted = extract_pdfs(pdfs, output_dir="./extracted/")
"""

from cninfo_toolkit._utils import (
    is_valid_ts_code,
    parse_ts_code_list,
    sanitize_filename,
)
from cninfo_toolkit.anns import (
    Announcement,
    batch_query,
    format_markdown_summary,
    get_announcements,
)
from cninfo_toolkit.pdf_dl import (
    build_pdf_path,
    download_pdf,
    download_pdfs,
)
from cninfo_toolkit.pdf_extract import (
    build_extracted_path,
    extract_pdf,
    extract_pdfs,
)

__version__ = "0.1.0"
__author__ = "chenliitaz"
__email__ = "chenliitaz@gmail.com"

__all__ = [
    # ── anns ──
    "Announcement",
    "batch_query",
    "format_markdown_summary",
    "get_announcements",
    # ── pdf_dl ──
    "download_pdf",
    "download_pdfs",
    "build_pdf_path",
    # ── pdf_extract ──
    "extract_pdf",
    "extract_pdfs",
    "build_extracted_path",
    # ── utils ──
    "is_valid_ts_code",
    "parse_ts_code_list",
    "sanitize_filename",
    # ── metadata ──
    "__version__",
]
