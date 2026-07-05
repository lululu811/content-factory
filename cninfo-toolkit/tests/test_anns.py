"""Tests for cninfo_toolkit.anns."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from cninfo_toolkit.anns import (
    _ORG_ID_CACHE,  # noqa: F401
    Announcement,
    batch_query,
    format_markdown_summary,
    get_announcements,
)


class TestAnnouncement:
    def test_to_dict(self, sample_announcement_raw):
        ann = Announcement.from_api_response(
            sample_announcement_raw, ts_code="600487.SH", org_id="gssh0600487"
        )
        d = ann.to_dict()
        assert d["ann_id"] == "1225380372"
        assert d["ts_code"] == "600487.SH"
        assert d["org_id"] == "gssh0600487"
        assert d["ann_date"] == "2024-06-23"
        assert d["title"] == "Test Announcement"
        assert "1225380372.PDF" in d["url"]
        assert d["sec_code"] == "600487"

    def test_from_api_empty_adjunct_url(self):
        raw = {
            "announcementId": "123",
            "announcementTitle": "Test",
            "announcementTime": 1719120000000,
            "adjunctUrl": "",
            "secCode": "600487",
        }
        ann = Announcement.from_api_response(raw, "600487.SH", "gssh0600487")
        assert ann.url == ""


class TestGetAnnouncements:
    def test_invalid_ts_code_raises(self):
        with pytest.raises(ValueError, match="Invalid TS code"):
            get_announcements("invalid_code")

    def test_org_id_not_found_returns_empty(
        self,
        sample_api_response,  # noqa: F811
    ):
        # No mock → _get_org_id returns None → empty list
        # First call to cninfo will try network, but _get_org_id caches None
        # We need to patch the network call
        with patch("cninfo_toolkit.anns._get_org_id", return_value=None):
            result = get_announcements("600487.SH", days=14)
        assert result == []

    def test_returns_announcements(self, sample_api_response, sample_org_id_response):
        with (
            patch("cninfo_toolkit.anns._get_org_id", return_value="gssh0600487"),
            patch("cninfo_toolkit.anns.post_json", return_value=sample_api_response),
        ):
            anns = get_announcements("600487.SH", days=14)
        assert len(anns) == 1
        assert anns[0].ts_code == "600487.SH"
        assert anns[0].ann_date == "2024-06-23"

    def test_custom_date_range(self, sample_api_response, sample_org_id_response):
        with (
            patch("cninfo_toolkit.anns._get_org_id", return_value="gssh0600487"),
            patch("cninfo_toolkit.anns.post_json", return_value=sample_api_response) as mock_post,
        ):
            get_announcements(
                "600487.SH",
                days=14,
                start_date="2024-01-01",
                end_date="2024-01-31",
            )
        # post_json is called as post_json(url, data) — second positional arg is the data
        call_args = mock_post.call_args
        data = call_args.args[1]  # Second positional arg
        assert "2024-01-01~2024-01-31" in data["seDate"]


class TestBatchQuery:
    def test_multiple_companies(self, sample_api_response, sample_org_id_response):
        with (
            patch("cninfo_toolkit.anns._get_org_id", return_value="gssh0600487"),
            patch("cninfo_toolkit.anns.post_json", return_value=sample_api_response),
        ):
            results = batch_query(
                ["600487.SH", "300308.SZ"],
                days=14,
                rate_limit=0,  # speed up tests
            )
        assert "600487.SH" in results
        assert "300308.SZ" in results
        assert len(results["600487.SH"]) == 1


class TestFormatMarkdownSummary:
    def test_basic(self, sample_announcement_raw):
        ann = Announcement.from_api_response(sample_announcement_raw, "600487.SH", "gssh0600487")
        output = format_markdown_summary(
            {"600487.SH": [ann]},
            title="Test Summary",
        )
        assert "Test Summary" in output
        assert "600487.SH" in output
        assert "Test Announcement" in output

    def test_empty_results(self):
        output = format_markdown_summary({})
        assert "0 条公告" in output

    def test_truncates_long_lists(self, sample_announcement_raw):
        anns = [
            Announcement.from_api_response(sample_announcement_raw, "600487.SH", "gssh0600487")
            for _ in range(20)
        ]
        output = format_markdown_summary({"600487.SH": anns})
        assert "+10 more" in output  # Truncated to first 10
