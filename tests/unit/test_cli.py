"""Tests for content_factory.cli."""

from __future__ import annotations

from typer.testing import CliRunner

from content_factory.cli import app


runner = CliRunner()


class TestVersionCommand:
    def test_version(self):
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "content-factory" in result.stdout


class TestHelp:
    def test_root_help(self):
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "content-factory" in result.stdout

    def test_compliance_help(self):
        result = runner.invoke(app, ["compliance", "--help"])
        assert result.exit_code == 0

    def test_images_help(self):
        result = runner.invoke(app, ["images", "--help"])
        assert result.exit_code == 0


class TestComplianceCommand:
    def test_missing_article(self, tmp_path, monkeypatch):
        # Patch CF_ROOT to a temp dir to avoid looking at real drafts/
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["compliance", "nonexistent-slug"])
        # Should fail because article not found
        assert result.exit_code != 0
