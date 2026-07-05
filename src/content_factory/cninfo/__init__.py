"""cninfo (巨潮资讯网) integration for content-factory.

Public API is re-exported from the submodules for convenience.
"""

from content_factory.cninfo._utils import (
    is_valid_ts_code,
    parse_ts_code_list,
    sanitize_filename,
)
from content_factory.cninfo.anns import (
    Announcement,
    batch_query,
    format_markdown_summary,
    get_announcements,
)
from content_factory.cninfo.pdf_dl import (
    BatchDownloadReport,
    DownloadResult,
    build_pdf_path,
    download_pdf,
    download_pdfs,
)
from content_factory.cninfo.pdf_extract import (
    BatchExtractionReport,
    ExtractionResult,
    build_extracted_path,
    extract_pdf,
    extract_pdfs,
)

__all__ = [
    # anns
    "Announcement",
    "batch_query",
    "format_markdown_summary",
    "get_announcements",
    # pdf_dl
    "BatchDownloadReport",
    "DownloadResult",
    "build_pdf_path",
    "download_pdf",
    "download_pdfs",
    # pdf_extract
    "BatchExtractionReport",
    "ExtractionResult",
    "build_extracted_path",
    "extract_pdf",
    "extract_pdfs",
    # utils
    "is_valid_ts_code",
    "parse_ts_code_list",
    "sanitize_filename",
]
