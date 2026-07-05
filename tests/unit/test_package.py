"""Tests for content_factory package metadata."""

from __future__ import annotations

import content_factory


class TestContentFactoryMetadata:
    def test_version_is_string(self):
        assert isinstance(content_factory.__version__, str)

    def test_version_format(self):
        # Should be semver: "X.Y.Z"
        parts = content_factory.__version__.split(".")
        assert len(parts) == 3
        assert all(p.isdigit() for p in parts)

    def test_submodules_exposed(self):
        expected = {"cninfo", "compliance", "images", "research", "pipeline", "utils"}
        actual = set(content_factory.__all__)
        assert expected.issubset(actual), f"Missing submodules: {expected - actual}"

    def test_author_and_email(self):
        assert content_factory.__author__ == "chenliitaz"
        assert "@" in content_factory.__email__


class TestCli:
    def test_cli_app_exists(self):
        from content_factory.cli import app

        assert app is not None
        assert app.info.name == "cf"

    def test_version_command(self):
        from typer.testing import CliRunner

        from content_factory.cli import app

        runner = CliRunner()
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "content-factory" in result.stdout
