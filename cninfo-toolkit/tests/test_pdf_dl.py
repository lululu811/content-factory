"""Tests for cninfo_toolkit.pdf_dl."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from cninfo_toolkit.anns import Announcement
from cninfo_toolkit.pdf_dl import (
    build_pdf_path,
    download_pdf,
    download_pdfs,
)

SAMPLE_PDF_URL = "http://static.cninfo.com.cn/finalpage/2026-06-23/1225380372.PDF"


@pytest.fixture
def sample_ann() -> Announcement:
    return Announcement(
        ann_id="1225380372",
        ts_code="600487.SH",
        org_id="gssh0600487",
        ann_date="2026-06-23",
        title="Test Announcement",
        url=SAMPLE_PDF_URL,
        sec_code="600487",
    )


class TestDownloadPdf:
    def test_success(self, tmp_output_dir, sample_pdf_bytes):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = sample_pdf_bytes

        with patch("cninfo_toolkit.pdf_dl.requests.get", return_value=mock_response):
            output = tmp_output_dir / "test.PDF"
            success = download_pdf(SAMPLE_PDF_URL, output)
        assert success
        assert output.exists()
        assert output.read_bytes() == sample_pdf_bytes

    def test_invalid_pdf_rejected(self, tmp_output_dir):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"<html>not a pdf</html>"

        with patch("cninfo_toolkit.pdf_dl.requests.get", return_value=mock_response):
            output = tmp_output_dir / "bad.PDF"
            success = download_pdf(SAMPLE_PDF_URL, output)
        assert not success

    def test_http_error(self, tmp_output_dir):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.content = b""

        with patch("cninfo_toolkit.pdf_dl.requests.get", return_value=mock_response):
            output = tmp_output_dir / "test.PDF"
            success = download_pdf(SAMPLE_PDF_URL, output)
        assert not success

    def test_request_exception(self, tmp_output_dir):
        import requests

        with patch(
            "cninfo_toolkit.pdf_dl.requests.get",
            side_effect=requests.RequestException("network error"),
        ):
            output = tmp_output_dir / "test.PDF"
            success = download_pdf(SAMPLE_PDF_URL, output, retries=2)
        assert not success


class TestBuildPdfPath:
    def test_basic(self, tmp_output_dir):
        path = build_pdf_path(
            tmp_output_dir,
            "600487.SH",
            "2026-06-23",
            "Test Announcement",
        )
        assert path.name == "600487.SH_20260623_Test Announcement.PDF"

    def test_sanitizes_invalid_chars(self, tmp_output_dir):
        path = build_pdf_path(
            tmp_output_dir,
            "600487.SH",
            "2026-06-23",
            "Foo/Bar:Baz?",
        )
        assert "Foo-Bar-Baz" in path.name


class TestDownloadPdfs:
    def test_batch_success(self, tmp_output_dir, sample_pdf_bytes, sample_ann):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = sample_pdf_bytes

        with patch("cninfo_toolkit.pdf_dl.requests.get", return_value=mock_response):
            report = download_pdfs(
                [sample_ann],
                output_dir=tmp_output_dir,
                rate_limit=0,
            )

        assert report.success_count == 1
        assert report.failed_count == 0
        assert report.total_count == 1

    def test_skip_existing(self, tmp_output_dir, sample_pdf_bytes, sample_ann):
        # Create the file first
        output_path = build_pdf_path(
            tmp_output_dir, sample_ann.ts_code, sample_ann.ann_date, sample_ann.title
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(sample_pdf_bytes)

        # Should skip without calling requests.get
        with patch("cninfo_toolkit.pdf_dl.requests.get") as mock_get:
            report = download_pdfs(
                [sample_ann],
                output_dir=tmp_output_dir,
                skip_existing=True,
                rate_limit=0,
            )

        assert report.skipped_count == 1
        assert mock_get.call_count == 0

    def test_empty_url(self, tmp_output_dir, sample_pdf_bytes):
        ann = Announcement(
            ann_id="x",
            ts_code="600487.SH",
            org_id="x",
            ann_date="2026-06-23",
            title="Test",
            url="",  # empty
            sec_code="600487",
        )
        report = download_pdfs([ann], output_dir=tmp_output_dir, rate_limit=0)
        assert report.failed_count == 1
        assert report.results[0].error == "empty url"

    def test_max_downloads(self, tmp_output_dir, sample_pdf_bytes, sample_ann):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = sample_pdf_bytes

        with patch("cninfo_toolkit.pdf_dl.requests.get", return_value=mock_response):
            report = download_pdfs(
                [sample_ann, sample_ann, sample_ann],
                output_dir=tmp_output_dir,
                rate_limit=0,
                max_downloads=1,
            )
        assert report.success_count == 1
