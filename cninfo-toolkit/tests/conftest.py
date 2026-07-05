"""Shared pytest fixtures for cninfo-toolkit tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def sample_announcement_raw() -> dict:
    """Sample raw API response item."""
    return {
        "announcementId": "1225380372",
        "announcementTitle": "Test Announcement",
        "announcementTime": 1719120000000,  # 2024-06-23 00:00:00 UTC
        "adjunctUrl": "finalpage/2024-06-23/1225380372.PDF",
        "secCode": "600487",
    }


@pytest.fixture
def sample_org_id_response() -> dict:
    """Sample szse_stock.json response."""
    return {
        "stockList": [
            {"code": "600487", "orgId": "gssh0600487"},
            {"code": "300308", "orgId": "9900012345"},
        ]
    }


@pytest.fixture
def sample_api_response(sample_announcement_raw) -> dict:
    """Sample cninfo POST API response."""
    return {
        "announcements": [sample_announcement_raw],
        "totalAnnouncement": 1,
    }


@pytest.fixture
def tmp_output_dir(tmp_path: Path) -> Path:
    """Temporary output directory."""
    output = tmp_path / "output"
    output.mkdir()
    return output


@pytest.fixture
def sample_pdf_bytes() -> bytes:
    """Minimal valid PDF bytes — >1KB to pass download size check."""
    # Minimal PDF: %PDF-1.4 ... %%EOF
    # Padded to >1KB so download_pdf's size check passes
    pdf = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n1 0 obj\n<<>>\nendobj\n"
    pdf += b"% padding to make > 1KB for download size check\n" * 30
    pdf += b"trailer\n<<>>\n%%EOF\n"
    return pdf
