"""PDF extraction API for cninfo announcement PDFs.

This module uses pdfplumber to extract text and tables from announcement PDFs,
with built-in protection against out-of-memory crashes for large files.

Example:
    >>> from pathlib import Path
    >>> from cninfo_toolkit import extract_pdf, extract_pdfs
    >>> # Single extraction
    >>> result = extract_pdf(Path("./announcement.PDF"))
    >>> print(f"Extracted {result['page_count']} pages")
    >>> # Batch extraction
    >>> pdfs = list(Path("./pdfs/").glob("*.PDF"))
    >>> results = extract_pdfs(pdfs, output_dir=Path("./extracted/"))
"""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import pdfplumber

# ── Constants ────────────────────────────────────────────────────────────────

DEFAULT_SIZE_THRESHOLD_KB = 100
"""File size threshold above which the max-pages limit is enforced."""

DEFAULT_MAX_PAGES = 30
"""Default maximum pages to extract from large PDFs (prevents OOM)."""

EXTRACTOR_VERSION = "1.0.0"
"""Extractor version (bumped when extraction logic changes)."""


# ── Data model ───────────────────────────────────────────────────────────────


@dataclass
class ExtractionResult:
    """Result of extracting a single PDF.

    Attributes:
        pdf_path: The source PDF path.
        page_count: Total pages in the PDF.
        pages_processed: Pages actually extracted (may be < page_count if truncated).
        truncated: True if max-pages limit was hit.
        file_size_kb: PDF size in KB.
        full_text: Extracted text with "=== Page N ===" headers.
        tables: List of extracted tables, each as a dict with 'page' and 'rows'.
        table_count: Number of extracted tables.
        error: Error message (empty on success).
    """

    pdf_path: str
    page_count: int = 0
    pages_processed: int = 0
    truncated: bool = False
    file_size_kb: float = 0.0
    full_text: str = ""
    tables: list[dict[str, Any]] = field(default_factory=list)
    table_count: int = 0
    error: str = ""

    @property
    def success(self) -> bool:
        """Whether extraction succeeded (no error)."""
        return not self.error

    def to_dict(self) -> dict[str, Any]:
        """Convert to a dict (for JSON serialization)."""
        return asdict(self)


# ── Core extraction ──────────────────────────────────────────────────────────


def extract_pdf(
    pdf_path: Path,
    *,
    max_pages: int = DEFAULT_MAX_PAGES,
    size_threshold_kb: int = DEFAULT_SIZE_THRESHOLD_KB,
) -> ExtractionResult:
    """Extract text and tables from a single PDF.

    Args:
        pdf_path: Path to the PDF file.
        max_pages: Maximum pages to extract (enforced when file is large).
        size_threshold_kb: File size threshold (KB) above which max-pages is enforced.

    Returns:
        ExtractionResult with all extracted data. Check `.success` and `.error`.

    Examples:
        >>> from pathlib import Path
        >>> result = extract_pdf(Path("./announcement.PDF"))
        >>> if result.success:
        ...     print(f"{result.page_count} pages, {result.table_count} tables")
    """
    pdf_path_str = str(pdf_path)
    if not Path(pdf_path_str).exists():
        return ExtractionResult(pdf_path=pdf_path_str, error=f"PDF not found: {pdf_path_str}")

    file_size_kb = Path(pdf_path_str).stat().st_size / 1024
    truncated = file_size_kb > size_threshold_kb

    actual_max_pages = max_pages if truncated else 9999

    full_text_parts: list[str] = []
    tables: list[dict[str, Any]] = []
    page_count = 0

    try:
        with pdfplumber.open(pdf_path_str) as pdf:
            page_count = len(pdf.pages)
            pages_to_process = min(page_count, actual_max_pages)

            for i in range(pages_to_process):
                page = pdf.pages[i]

                text = page.extract_text() or ""
                if text:
                    full_text_parts.append(f"=== Page {i + 1} ===\n{text}")

                page_tables = page.extract_tables()
                for t in page_tables:
                    if t:
                        tables.append(
                            {
                                "page": i + 1,
                                "rows": [
                                    [cell.strip() if cell else "" for cell in row] for row in t
                                ],
                            }
                        )
    except Exception as exc:
        return ExtractionResult(
            pdf_path=pdf_path_str,
            file_size_kb=round(file_size_kb, 2),
            error=f"{type(exc).__name__}: {exc}",
        )

    return ExtractionResult(
        pdf_path=pdf_path_str,
        page_count=page_count,
        pages_processed=pages_to_process,
        truncated=truncated,
        file_size_kb=round(file_size_kb, 2),
        full_text="\n\n".join(full_text_parts),
        tables=tables,
        table_count=len(tables),
    )


# ── Output path ──────────────────────────────────────────────────────────────


def build_extracted_path(output_dir: Path, pdf_path: Path) -> Path:
    """Construct the output JSON path for an extracted PDF.

    Format: `{output_dir}/{pdf_stem}.json`

    Args:
        output_dir: Base output directory.
        pdf_path: Source PDF path.

    Returns:
        Full output JSON path.
    """
    return output_dir / f"{pdf_path.stem}.json"


# ── Batch extraction ─────────────────────────────────────────────────────────


@dataclass
class BatchExtractionReport:
    """Aggregate report of a batch PDF extraction.

    Attributes:
        success_count: Number of successful extractions.
        skipped_count: Number of files skipped (already extracted).
        failed_count: Number of failed extractions.
        total_count: Total number of extraction attempts.
        results: List of individual ExtractionResult objects.
        extracted_at: ISO 8601 timestamp of completion.
    """

    success_count: int = 0
    skipped_count: int = 0
    failed_count: int = 0
    total_count: int = 0
    results: list[ExtractionResult] = field(default_factory=list)
    extracted_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to a dict (for JSON serialization)."""
        return {
            "extracted_at": self.extracted_at,
            "total_count": self.total_count,
            "success_count": self.success_count,
            "skipped_count": self.skipped_count,
            "failed_count": self.failed_count,
            "results": [r.to_dict() for r in self.results],
        }


def extract_pdfs(
    pdfs: list[Path],
    output_dir: Path,
    *,
    skip_existing: bool = True,
    max_pages: int = DEFAULT_MAX_PAGES,
    size_threshold_kb: int = DEFAULT_SIZE_THRESHOLD_KB,
    rate_limit: float = 0.3,
) -> BatchExtractionReport:
    """Extract text and tables from a batch of PDFs.

    Args:
        pdfs: List of PDF paths.
        output_dir: Where to write extracted JSON files (created if needed).
        skip_existing: If True, skip files that already have a valid JSON output.
        max_pages: Maximum pages to extract per PDF (when large).
        size_threshold_kb: File size threshold for triggering max-pages limit.
        rate_limit: Seconds to sleep between extractions (default 0.3s, prevents memory pressure).

    Returns:
        BatchExtractionReport with detailed per-file results.

    Examples:
        >>> from pathlib import Path
        >>> pdfs = list(Path("./pdfs/").glob("*.PDF"))
        >>> report = extract_pdfs(pdfs, output_dir=Path("./extracted/"))
        >>> print(f"Extracted {report.success_count}/{report.total_count}")
    """
    import json
    import sys

    output_dir.mkdir(parents=True, exist_ok=True)
    report = BatchExtractionReport(total_count=len(pdfs))

    for i, pdf_path in enumerate(pdfs, 1):
        output_path = build_extracted_path(output_dir, pdf_path)

        if skip_existing and output_path.exists():
            result = ExtractionResult(pdf_path=str(pdf_path))
            report.results.append(result)
            report.skipped_count += 1
            print(
                f"[{i}/{report.total_count}] {pdf_path.name} ⏭️  already extracted",
                file=sys.stderr,
            )
            continue

        size_kb = pdf_path.stat().st_size / 1024
        print(
            f"[{i}/{report.total_count}] {pdf_path.name} ({size_kb:.1f}KB) ... ",
            end="",
            file=sys.stderr,
        )

        result = extract_pdf(pdf_path, max_pages=max_pages, size_threshold_kb=size_threshold_kb)

        if result.success:
            output_path.write_text(
                json.dumps(result.to_dict(), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            report.success_count += 1
            trunc_marker = " [truncated]" if result.truncated else ""
            print(f"✅ {result.page_count}p / {result.table_count}t{trunc_marker}", file=sys.stderr)
        else:
            report.failed_count += 1
            print(f"❌ {result.error}", file=sys.stderr)

        report.results.append(result)

        if i < report.total_count:
            time.sleep(rate_limit)

    report.extracted_at = datetime.now().isoformat()
    return report


__all__ = [
    "ExtractionResult",
    "BatchExtractionReport",
    "build_extracted_path",
    "extract_pdf",
    "extract_pdfs",
    "DEFAULT_MAX_PAGES",
    "DEFAULT_SIZE_THRESHOLD_KB",
    "EXTRACTOR_VERSION",
]
