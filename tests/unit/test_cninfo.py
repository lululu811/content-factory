"""Tests for content_factory.cninfo subpackage.

This file re-tests the cninfo module within the new content_factory package
to verify the import path migration works correctly.
"""

from __future__ import annotations

import pytest

from content_factory import cninfo
from content_factory.cninfo import (
    Announcement,
    batch_query,
    format_markdown_summary,
    get_announcements,
    is_valid_ts_code,
    parse_ts_code_list,
    sanitize_filename,
)


class TestTsCodeValidation:
    @pytest.mark.parametrize(
        "code",
        ["600487.SH", "300308.SZ", "688498.SH", "920438.BJ"],
    )
    def test_valid_codes(self, code):
        assert is_valid_ts_code(code)

    @pytest.mark.parametrize(
        "code",
        ["600487", "600487.sh", "600487.AB", "12345.SH", ""],
    )
    def test_invalid_codes(self, code):
        assert not is_valid_ts_code(code)


class TestCodeListParsing:
    def test_newline_separated(self):
        text = "600487.SH\n300308.SZ\n000070.SZ"
        assert parse_ts_code_list(text) == ["600487.SH", "300308.SZ", "000070.SZ"]

    def test_filter_invalid(self):
        text = "garbage\n600487.SH\nmore garbage\n300308"
        assert parse_ts_code_list(text) == ["600487.SH"]


class TestSanitizeFilename:
    def test_basic(self):
        assert sanitize_filename("normal title") == "normal title"

    def test_invalid_chars(self):
        assert sanitize_filename("foo/bar:baz") == "foo-bar-baz"

    def test_max_length(self):
        assert sanitize_filename("a" * 100, max_length=10) == "a" * 10

    def test_empty_fallback(self):
        assert sanitize_filename("") == "untitled"
        assert sanitize_filename("///") == "untitled"


class TestGetAnnouncements:
    def test_invalid_code_raises(self):
        with pytest.raises(ValueError, match="Invalid TS code"):
            get_announcements("invalid_code")

    def test_org_id_not_found_returns_empty(self):
        from unittest.mock import patch

        from content_factory.cninfo.anns import _ORG_ID_CACHE

        _ORG_ID_CACHE.clear()
        with patch("content_factory.cninfo.anns._get_org_id", return_value=None):
            result = get_announcements("600487.SH", days=14)
        assert result == []


class TestBatchQuery:
    def test_returns_dict(self):
        from unittest.mock import patch

        from content_factory.cninfo.anns import _ORG_ID_CACHE

        _ORG_ID_CACHE.clear()
        with (
            patch("content_factory.cninfo.anns._get_org_id", return_value="gssh0600487"),
            patch("content_factory.cninfo.anns.post_json", return_value={"announcements": []}),
        ):
            results = batch_query(["600487.SH", "300308.SZ"], days=14, rate_limit=0)
        assert "600487.SH" in results
        assert "300308.SZ" in results


class TestFormatMarkdownSummary:
    def test_basic(self, sample_announcement_raw):
        ann = Announcement.from_api_response(
            sample_announcement_raw, "600487.SH", "gssh0600487"
        )
        output = format_markdown_summary({"600487.SH": [ann]}, title="Test")
        assert "Test" in output
        assert "600487.SH" in output
        assert "Test Announcement" in output


class TestPublicApiReExports:
    """Verify that content_factory.cninfo re-exports the public API."""

    def test_announcement_exported(self):
        assert hasattr(cninfo, "Announcement")

    def test_get_announcements_exported(self):
        assert hasattr(cninfo, "get_announcements")

    def test_batch_query_exported(self):
        assert hasattr(cninfo, "batch_query")

    def test_format_markdown_summary_exported(self):
        assert hasattr(cninfo, "format_markdown_summary")
