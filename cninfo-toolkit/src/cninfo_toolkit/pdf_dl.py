"""PDF download API for cninfo announcement URLs.

This module downloads PDFs from cninfo's static file server with rate limiting,
automatic retries, and integrity validation (PDF magic bytes).

Example:
    >>> from cninfo_toolkit import download_pdf, download_pdfs
    >>> # Single download
    >>> success = download_pdf(
    ...     "http://static.cninfo.com.cn/finalpage/2026-06-23/xxx.PDF",
    ...     Path("./announcement.PDF"),
    ... )
    >>> # Batch download from announcements
    >>> from cninfo_toolkit import get_announcements
    >>> anns = get_announcements("600487.SH", days=14)
    >>> results = download_pdfs(anns, output_dir=Path("./pdfs/"))
"""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any

import requests

from cninfo_toolkit._utils import (
    DEFAULT_RATE_LIMIT_SECONDS,
    DEFAULT_RETRIES,
    DEFAULT_TIMEOUT,
    DEFAULT_USER_AGENT,
    sanitize_filename,
)

if TYPE_CHECKING:
    from pathlib import Path

# ── Data model ───────────────────────────────────────────────────────────────


@dataclass
class DownloadResult:
    """Result of a single PDF download attempt.

    Attributes:
        ann_id: The cninfo announcement ID (from Announcement.ann_id).
        ts_code: The TS-format stock code.
        ann_date: The announcement date.
        title: The announcement title.
        url: The original PDF URL.
        local_path: The local file path (empty if failed).
        size_kb: The downloaded file size in KB (0 if failed).
        skipped: True if the file already existed and was skipped.
        error: Error message (empty on success).
    """

    ann_id: str
    ts_code: str
    ann_date: str
    title: str
    url: str
    local_path: str = ""
    size_kb: int = 0
    skipped: bool = False
    error: str = ""

    @property
    def success(self) -> bool:
        """Whether the download succeeded (or was skipped)."""
        return bool(self.local_path) and not self.error

    def to_dict(self) -> dict[str, Any]:
        """Convert to a dict (for JSON serialization)."""
        return asdict(self)


# ── Single download ──────────────────────────────────────────────────────────


_PDF_MAGIC = b"%PDF"
"""First 4 bytes of a valid PDF file."""


def download_pdf(
    url: str,
    output_path: Path,
    *,
    timeout: int = DEFAULT_TIMEOUT,
    retries: int = DEFAULT_RETRIES,
) -> bool:
    """Download a single PDF with retries and integrity validation.

    Args:
        url: The PDF URL (typically http://static.cninfo.com.cn/...PDF).
        output_path: Where to save the PDF.
        timeout: HTTP timeout per attempt in seconds.
        retries: Number of retries on failure.

    Returns:
        True on success, False on failure.

    Examples:
        >>> from pathlib import Path
        >>> success = download_pdf(
        ...     "http://static.cninfo.com.cn/finalpage/2026-06-23/xxx.PDF",
        ...     Path("./announcement.PDF"),
        ... )
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    headers = {
        "User-Agent": DEFAULT_USER_AGENT,
        "Referer": "http://www.cninfo.com.cn/",
    }

    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(
                url,
                headers=headers,
                timeout=timeout,
                allow_redirects=True,
            )
            if (
                resp.status_code == 200
                and len(resp.content) > 1024
                and resp.content[:4] == _PDF_MAGIC
            ):
                output_path.write_bytes(resp.content)
                return True
        except requests.RequestException:
            pass

        if attempt < retries:
            time.sleep(2**attempt)  # Exponential backoff

    return False


# ── Path construction ────────────────────────────────────────────────────────


def build_pdf_path(
    output_dir: Path,
    ts_code: str,
    ann_date: str,
    title: str,
) -> Path:
    """Construct a deterministic PDF output path.

    Format: `{output_dir}/{ts_code}_{YYYYMMDD}_{title_slug}.PDF`

    Args:
        output_dir: Base output directory.
        ts_code: TS-format stock code.
        ann_date: Announcement date in YYYY-MM-DD format.
        title: Announcement title (sanitized).

    Returns:
        Full output path.
    """
    slug = sanitize_filename(title)
    date_compact = ann_date.replace("-", "")
    return output_dir / f"{ts_code}_{date_compact}_{slug}.PDF"


# ── Batch download ───────────────────────────────────────────────────────────


@dataclass
class BatchDownloadReport:
    """Aggregate report of a batch download.

    Attributes:
        success_count: Number of successful downloads.
        skipped_count: Number of files skipped (already existed).
        failed_count: Number of failed downloads.
        total_count: Total number of download attempts.
        results: List of individual DownloadResult objects.
        downloaded_at: ISO 8601 timestamp of completion.
    """

    success_count: int = 0
    skipped_count: int = 0
    failed_count: int = 0
    total_count: int = 0
    results: list[DownloadResult] = field(default_factory=list)
    downloaded_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to a dict (for JSON serialization)."""
        return {
            "downloaded_at": self.downloaded_at,
            "total_count": self.total_count,
            "success_count": self.success_count,
            "skipped_count": self.skipped_count,
            "failed_count": self.failed_count,
            "results": [r.to_dict() for r in self.results],
        }


def download_pdfs(
    anns: list[Any],  # list[Announcement] but avoiding import cycle
    output_dir: Path,
    *,
    skip_existing: bool = True,
    rate_limit: float = DEFAULT_RATE_LIMIT_SECONDS,
    timeout: int = DEFAULT_TIMEOUT,
    retries: int = DEFAULT_RETRIES,
    max_downloads: int = 0,
) -> BatchDownloadReport:
    """Download a batch of announcement PDFs.

    Each Announcement must expose `.ann_id`, `.ts_code`, `.ann_date`, `.title`,
    `.url` (typically a `cninfo_toolkit.Announcement`).

    Args:
        anns: List of Announcement-like objects.
        output_dir: Base output directory (created if needed).
        skip_existing: If True, skip files that already exist and are valid (>1KB).
        rate_limit: Seconds to sleep between downloads (default 0.5s).
        timeout: HTTP timeout per attempt in seconds.
        retries: Number of retries per download.
        max_downloads: If >0, stop after this many downloads.

    Returns:
        BatchDownloadReport with detailed per-file results.

    Examples:
        >>> from pathlib import Path
        >>> from cninfo_toolkit import get_announcements, download_pdfs
        >>> anns = get_announcements("600487.SH", days=14)
        >>> report = download_pdfs(anns, output_dir=Path("./pdfs/"))
        >>> print(f"Downloaded {report.success_count}/{report.total_count}")
    """
    import sys

    output_dir.mkdir(parents=True, exist_ok=True)
    report = BatchDownloadReport(total_count=len(anns))

    for i, ann in enumerate(anns, 1):
        if max_downloads > 0 and (report.success_count + report.failed_count) >= max_downloads:
            break

        result = DownloadResult(
            ann_id=getattr(ann, "ann_id", ""),
            ts_code=getattr(ann, "ts_code", ""),
            ann_date=getattr(ann, "ann_date", ""),
            title=getattr(ann, "title", ""),
            url=getattr(ann, "url", ""),
        )

        if not result.url:
            result.error = "empty url"
            report.results.append(result)
            report.failed_count += 1
            continue

        output_path = build_pdf_path(
            output_dir,
            getattr(ann, "ts_code", ""),
            getattr(ann, "ann_date", ""),
            getattr(ann, "title", ""),
        )

        # Skip if exists
        if skip_existing and output_path.exists():
            size = output_path.stat().st_size
            if size > 1024:
                result.local_path = str(output_path)
                result.size_kb = size // 1024
                result.skipped = True
                report.results.append(result)
                report.skipped_count += 1
                print(
                    f"[{i}/{report.total_count}] {result.ts_code} {result.ann_date} "
                    f"⏭️  skipped ({result.size_kb}KB)",
                    file=sys.stderr,
                )
                continue

        # Download
        print(
            f"[{i}/{report.total_count}] {result.ts_code} {result.ann_date} ⬇️  {result.title[:40]}",
            end=" ... ",
            file=sys.stderr,
        )
        if download_pdf(result.url, output_path, timeout=timeout, retries=retries):
            size = output_path.stat().st_size
            result.local_path = str(output_path)
            result.size_kb = size // 1024
            report.success_count += 1
            print(f"✅ {result.size_kb}KB", file=sys.stderr)
        else:
            # Clean up partial file
            if output_path.exists():
                output_path.unlink()
            result.error = "download failed"
            report.failed_count += 1
            print(f"❌ {result.error}", file=sys.stderr)

        report.results.append(result)

        if i < report.total_count:
            time.sleep(rate_limit)

    report.downloaded_at = datetime.now().isoformat()
    return report


__all__ = [
    "DEFAULT_RETRIES",
    "DownloadResult",
    "BatchDownloadReport",
    "build_pdf_path",
    "download_pdf",
    "download_pdfs",
]
