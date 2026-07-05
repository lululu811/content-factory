"""Tests for cninfo_toolkit.pdf_extract."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from cninfo_toolkit.pdf_extract import (
    build_extracted_path,
    extract_pdf,
    extract_pdfs,
)

if TYPE_CHECKING:
    from pathlib import Path

# ── Sample PDFs ────────────────────────────────────────────────────────────


def _create_minimal_pdf(path: Path, pages: int = 3, has_tables: bool = False) -> None:
    """Create a minimal but valid PDF for testing (using reportlab).

    Real pdfs would need tables; here we just create empty pages.
    """
    from reportlab.pdfgen import canvas

    c = canvas.Canvas(str(path))
    for i in range(pages):
        c.drawString(50, 750, f"Page {i + 1} content")
        c.showPage()
    c.save()


@pytest.fixture
def small_pdf(tmp_path: Path) -> Path:
    """Small PDF (well under size threshold)."""
    pdf = tmp_path / "small.PDF"
    _create_minimal_pdf(pdf, pages=2)
    return pdf


@pytest.fixture
def large_pdf(tmp_path: Path) -> Path:
    """PDF over the size threshold (>100KB)."""
    from reportlab.pdfgen import canvas

    pdf = tmp_path / "large.PDF"
    c = canvas.Canvas(str(pdf))
    # Many pages with substantial text to push size over 100KB
    for i in range(50):
        c.drawString(50, 750, f"Page {i + 1} content: " + "x" * 200)
        c.drawString(50, 730, "Another line of text content")
        c.drawString(50, 710, "Yet another line of text content")
        c.showPage()
    c.save()
    return pdf


# ── Tests ───────────────────────────────────────────────────────────────────


class TestExtractPdf:
    def test_success(self, small_pdf):
        result = extract_pdf(small_pdf)
        assert result.success
        assert result.page_count == 2
        assert result.pages_processed == 2
        assert not result.truncated
        assert "Page 1 content" in result.full_text
        assert "Page 2 content" in result.full_text

    def test_truncated_when_large(self, large_pdf):
        # Force the threshold low so we always trigger truncation
        result = extract_pdf(large_pdf, size_threshold_kb=1, max_pages=5)
        assert result.truncated
        assert result.pages_processed == 5
        assert result.pages_processed < result.page_count

    def test_not_found(self, tmp_path):
        result = extract_pdf(tmp_path / "nonexistent.PDF")
        assert not result.success
        assert "not found" in result.error

    def test_invalid_pdf(self, tmp_path):
        bad = tmp_path / "bad.PDF"
        bad.write_bytes(b"not a pdf at all")
        result = extract_pdf(bad)
        # pdfplumber will raise an error
        assert not result.success
        assert result.error != ""


class TestBuildExtractedPath:
    def test_basic(self, tmp_output_dir):
        pdf = tmp_output_dir / "ann.PDF"
        out = build_extracted_path(tmp_output_dir, pdf)
        assert out == tmp_output_dir / "ann.json"


class TestExtractPdfs:
    def test_batch_success(self, tmp_output_dir, small_pdf):
        pdfs = [small_pdf]
        report = extract_pdfs(pdfs, output_dir=tmp_output_dir, rate_limit=0)
        assert report.success_count == 1
        assert report.failed_count == 0

        # Output file should exist
        output_json = build_extracted_path(tmp_output_dir, small_pdf)
        assert output_json.exists()
        data = json.loads(output_json.read_text(encoding="utf-8"))
        assert data["page_count"] == 2
        assert data.get("success", True)  # No "success" key in JSON

    def test_skip_existing(self, tmp_output_dir, small_pdf):
        # Pre-create the JSON output
        output_json = build_extracted_path(tmp_output_dir, small_pdf)
        output_json.write_text('{"page_count": 0, "pre-existing": true}', encoding="utf-8")

        report = extract_pdfs(
            [small_pdf], output_dir=tmp_output_dir, skip_existing=True, rate_limit=0
        )
        assert report.skipped_count == 1
        # Should not have been overwritten
        assert "pre-existing" in output_json.read_text(encoding="utf-8")

    def test_invalid_pdf(self, tmp_output_dir):
        bad = tmp_output_dir / "bad.PDF"
        bad.write_bytes(b"not a pdf")

        report = extract_pdfs([bad], output_dir=tmp_output_dir, rate_limit=0)
        assert report.failed_count == 1
        assert report.results[0].error != ""
