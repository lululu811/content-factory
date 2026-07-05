"""Shared pytest fixtures for content-factory tests."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest


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
    pdf = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n1 0 obj\n<<>>\nendobj\n"
    pdf += b"% padding to make > 1KB for download size check\n" * 30
    pdf += b"trailer\n<<>>\n%%EOF\n"
    return pdf


@pytest.fixture
def sample_post_frontmatter() -> dict:
    """Sample article frontmatter for compliance tests."""
    return {
        "title": "光纤涨价是 beta,光模块才是 alpha — AI 算力下 18 家光通信公司反共识拆解",
        "verified_at": "2026-07-02",
        "data_sources": ["myMCP", "industry-kol-scan", "TrendForce"],
        "verified_sources": [
            {"url": "https://example.com/a", "title": "Source A", "verified_at": "2026-07-01"},
            {"url": "https://example.com/b", "title": "Source B", "verified_at": "2026-07-01"},
        ],
        "verified_companies": [
            "- 600487.SH 亨通光电",
            "- 300308.SZ 中际旭创",
        ],
        "a2_candidates": {
            "layer1_原材料": ["603688.SH 石英股份"],
            "layer2_光纤": ["601869.SH 长飞光纤"],
        },
    }
