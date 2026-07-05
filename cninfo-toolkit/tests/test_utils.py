"""Tests for cninfo_toolkit._utils."""

from __future__ import annotations

import pytest

from cninfo_toolkit._utils import (
    detect_exchange,
    ensure_directory,
    is_valid_ts_code,
    parse_ts_code_list,
    sanitize_filename,
)


class TestIsValidTsCode:
    def test_valid_shanghai(self):
        assert is_valid_ts_code("600487.SH")

    def test_valid_shenzhen(self):
        assert is_valid_ts_code("300308.SZ")

    def test_valid_beijing(self):
        assert is_valid_ts_code("920438.BJ")

    def test_valid_kechuang(self):
        assert is_valid_ts_code("688498.SH")

    def test_invalid_no_dot(self):
        assert not is_valid_ts_code("600487")

    def test_invalid_lowercase(self):
        assert not is_valid_ts_code("600487.sh")

    def test_invalid_too_few_digits(self):
        assert not is_valid_ts_code("12345.SH")

    def test_invalid_too_many_digits(self):
        assert not is_valid_ts_code("1234567.SH")

    def test_invalid_wrong_letters(self):
        assert not is_valid_ts_code("600487.AB")

    def test_empty(self):
        assert not is_valid_ts_code("")


class TestParseTsCodeList:
    def test_newline_separated(self):
        text = "600487.SH\n300308.SZ\n000070.SZ"
        assert parse_ts_code_list(text) == ["600487.SH", "300308.SZ", "000070.SZ"]

    def test_comma_separated(self):
        text = "600487.SH, 300308.SZ, 000070.SZ"
        assert parse_ts_code_list(text) == ["600487.SH", "300308.SZ", "000070.SZ"]

    def test_mixed_separators(self):
        text = "600487.SH, 300308.SZ; 000070.SZ\n688498.SH"
        assert parse_ts_code_list(text) == [
            "600487.SH",
            "300308.SZ",
            "000070.SZ",
            "688498.SH",
        ]

    def test_filter_invalid(self):
        text = "garbage\n600487.SH\nmore garbage\n300308"
        assert parse_ts_code_list(text) == ["600487.SH"]

    def test_empty(self):
        assert parse_ts_code_list("") == []

    def test_whitespace_handling(self):
        text = "  600487.SH  ,\n  300308.SZ  "
        assert parse_ts_code_list(text) == ["600487.SH", "300308.SZ"]


class TestDetectExchange:
    @pytest.mark.parametrize(
        ("ts_code", "expected"),
        [
            ("600487.SH", "sse"),
            ("688498.SH", "sse"),
            ("601869.SH", "sse"),
            ("300308.SZ", "szse"),
            ("000070.SZ", "szse"),
            ("002491.SZ", "szse"),
            ("920438.BJ", "bj"),
            ("830799.BJ", "bj"),
            ("400001.BJ", "bj"),
        ],
    )
    def test_exchange_detection(self, ts_code, expected):
        assert detect_exchange(ts_code) == expected


class TestSanitizeFilename:
    def test_basic(self):
        assert sanitize_filename("normal title") == "normal title"

    def test_remove_invalid_chars(self):
        assert sanitize_filename("foo/bar:baz") == "foo-bar-baz"

    def test_max_length(self):
        assert sanitize_filename("a" * 100, max_length=10) == "a" * 10

    def test_strip_dots(self):
        assert sanitize_filename("...hidden...") == "hidden"

    def test_empty_fallback(self):
        assert sanitize_filename("") == "untitled"
        assert sanitize_filename("///") == "untitled"

    def test_collapse_whitespace(self):
        assert sanitize_filename("foo    bar\t\tbaz") == "foo bar baz"


class TestEnsureDirectory:
    def test_creates_directory(self, tmp_path):
        target = tmp_path / "nested" / "deeper"
        result = ensure_directory(target)
        assert result == target
        assert target.exists()

    def test_existing_directory(self, tmp_path):
        target = tmp_path / "existing"
        target.mkdir()
        result = ensure_directory(target)
        assert result == target
        assert target.exists()
