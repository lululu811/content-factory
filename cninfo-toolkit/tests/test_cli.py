"""Tests for the cninfo CLI."""

from __future__ import annotations

import json
from unittest.mock import patch

from typer.testing import CliRunner

from cninfo_toolkit._cli import app

runner = CliRunner()


class TestVersionCommand:
    def test_version_flag(self):
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "cninfo-toolkit" in result.stdout


class TestAnnsCommand:
    def test_no_codes_exits_error(self):
        result = runner.invoke(app, ["anns"])
        assert result.exit_code != 0

    def test_invalid_code_exits_error(self):
        result = runner.invoke(app, ["anns", "INVALID"])
        assert result.exit_code != 0

    def test_valid_code_markdown(self):
        with patch("cninfo_toolkit._cli.get_announcements") as mock:
            from cninfo_toolkit.anns import Announcement

            mock.return_value = [
                Announcement(
                    ann_id="123",
                    ts_code="600487.SH",
                    org_id="x",
                    ann_date="2026-06-23",
                    title="Test Title",
                    url="http://example.com/test.PDF",
                    sec_code="600487",
                )
            ]
            result = runner.invoke(app, ["anns", "600487.SH"])

        assert result.exit_code == 0
        assert "600487.SH" in result.stdout
        assert "Test Title" in result.stdout

    def test_valid_code_json(self):
        with patch("cninfo_toolkit._cli.get_announcements") as mock:
            from cninfo_toolkit.anns import Announcement

            mock.return_value = [
                Announcement(
                    ann_id="123",
                    ts_code="600487.SH",
                    org_id="x",
                    ann_date="2026-06-23",
                    title="Test",
                    url="http://example.com/test.PDF",
                    sec_code="600487",
                )
            ]
            result = runner.invoke(app, ["anns", "600487.SH", "--json"])

        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "600487.SH" in data
        assert len(data["600487.SH"]) == 1


class TestPdfDlCommand:
    def test_url_requires_output(self):
        result = runner.invoke(app, ["pdf-dl", "--url", "http://example.com/test.PDF"])
        assert result.exit_code != 0

    def test_requires_anns_or_url(self):
        result = runner.invoke(app, ["pdf-dl"])
        assert result.exit_code != 0

    def test_anns_file_not_found(self):
        result = runner.invoke(app, ["pdf-dl", "--anns", "/nonexistent.json"])
        assert result.exit_code != 0


class TestPipelineCommand:
    def test_no_codes_exits_error(self):
        result = runner.invoke(app, ["pipeline"])
        assert result.exit_code != 0

    def test_invalid_codes_exits_error(self):
        result = runner.invoke(app, ["pipeline", "INVALID"])
        assert result.exit_code != 0


class TestHelpText:
    def test_root_help(self):
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "cninfo" in result.stdout

    def test_anns_help(self):
        result = runner.invoke(app, ["anns", "--help"])
        assert result.exit_code == 0
        assert "--days" in result.stdout

    def test_pdf_dl_help(self):
        result = runner.invoke(app, ["pdf-dl", "--help"])
        assert result.exit_code == 0
        assert "--anns" in result.stdout

    def test_pdf_extract_help(self):
        result = runner.invoke(app, ["pdf-extract", "--help"])
        assert result.exit_code == 0
        assert "--pdf-dir" in result.stdout
