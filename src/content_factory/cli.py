"""Unified CLI for content-factory.

This module provides the `cf` command with subcommands:
- `cf anns`     — query A-share announcements from cninfo
- `cf pdf-dl`   — download announcement PDFs
- `cf pdf-extract` — extract text and tables from PDFs
- `cf pipeline` — run the full anns → pdf-dl → pdf-extract pipeline
- `cf compliance <slug>` — run compliance check on an article
- `cf images <type> --slug <slug>` — generate article images
- `cf research scan <topic>` — run industry KOL scan

After `pip install content-factory`, the `cf` command is available globally.

Examples:
    $ cf --version
    $ cf anns 600487.SH --days 14
    $ cf compliance ai-fiber-value-chain
    $ cf images bottleneck-matrix --slug ai-fiber-value-chain --data data.json
"""

from __future__ import annotations

import sys
from typing import Optional

import typer
from rich.console import Console

from content_factory import __version__
from content_factory.cninfo import _cli as cninfo_cli


app = typer.Typer(
    name="cf",
    help="content-factory: 投研型公众号深度文生产流水线。",
    no_args_is_help=True,
    rich_markup_mode="rich",
    add_completion=False,
    pretty_exceptions_enable=False,
)

console = Console()
err_console = Console(stderr=True)


def _version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"content-factory {__version__}")
        raise typer.Exit()


@app.callback()
def main_callback(
    version: bool = typer.Option(
        False,
        "--version",
        "-V",
        help="Show version and exit.",
        callback=_version_callback,
        is_eager=True,
    ),
) -> None:
    """content-factory: End-to-end content production pipeline for A-share newsletters."""


# ── Mount cninfo subcommands ──
# All `cf anns` / `cf pdf-dl` / `cf pdf-extract` / `cf pipeline` commands
# are provided by content_factory.cninfo._cli
for sub in ("anns", "pdf_dl", "pdf_extract", "pipeline"):
    if sub == "pdf_dl":
        sub_typer = getattr(cninfo_cli.app, "pdf_dl_cmd", None)  # type: ignore[attr-defined]
    elif sub == "pdf_extract":
        sub_typer = getattr(cninfo_cli.app, "pdf_extract_cmd", None)  # type: ignore[attr-defined]
    elif sub == "pipeline":
        sub_typer = getattr(cninfo_cli.app, "pipeline_cmd", None)  # type: ignore[attr-defined]
    else:
        sub_typer = getattr(cninfo_cli.app, f"{sub}_cmd", None)  # type: ignore[attr-defined]
    # Note: cninfo's CLI app is itself a Typer, not a single command.
    # We re-export the commands differently below.

# Since cninfo_cli.app is a Typer, we add its commands directly:
# The cleanest way: add cninfo_cli.app as a sub-typer.
app.add_typer(
    cninfo_cli.app,
    name="cninfo",
    help="Cninfo (巨潮资讯网) announcements: query, download, extract.",
)


# ── compliance ──


@app.command("compliance")
def compliance_cmd(
    slug: str = typer.Argument(..., help="Article slug (e.g., ai-fiber-value-chain)."),
    strict: bool = typer.Option(False, "--strict", help="Exit 1 on any FAIL."),
) -> None:
    """Run compliance check on an article.

    Examples:
        $ cf compliance ai-fiber-value-chain
        $ cf compliance ai-fiber-value-chain --strict
    """
    from content_factory.compliance import ComplianceChecker

    checker = ComplianceChecker(slug)
    result = checker.run()
    if strict and result.has_failures:
        raise typer.Exit(code=1)


# ── images ──


@app.command("images")
def images_cmd(
    chart_type: str = typer.Argument(
        ...,
        help="Chart type: bottleneck-matrix, 8layers, summary-dashboard, etc.",
    ),
    slug: str = typer.Option(..., "--slug", help="Article slug."),
    data: Optional[str] = typer.Option(None, "--data", help="Path to data JSON file."),
    output_dir: str = typer.Option("publish/images", "--output-dir", help="Output directory."),
) -> None:
    """Generate article images (matplotlib).

    Examples:
        $ cf images bottleneck-matrix --slug ai-fiber-value-chain --data data.json
        $ cf images summary-dashboard --slug ai-fiber-value-chain
    """
    from content_factory.images import ImageGenerator

    gen = ImageGenerator(slug=slug, output_dir=output_dir)
    gen.generate(chart_type=chart_type, data_path=data)


# ── research scan ──


@app.command("research")
def research_cmd(
    subcommand: str = typer.Argument("scan", help="Subcommand: scan."),
    topic: str = typer.Option(..., "--topic", help="Industry topic name."),
    slug: str = typer.Option(..., "--slug", help="Article slug for the raw output."),
) -> None:
    """Run research tools (industry KOL scan, data validation)."""
    if subcommand == "scan":
        from content_factory.research import KolScanner

        scanner = KolScanner(topic=topic, slug=slug)
        scanner.run()
    else:
        err_console.print(f"[red]Unknown subcommand:[/red] {subcommand}")
        raise typer.Exit(code=1)


# ── version / info ──


@app.command("version")
def version_cmd() -> None:
    """Show content-factory version."""
    console.print(f"content-factory {__version__}")
    console.print(f"Python {sys.version.split()[0]}")


if __name__ == "__main__":
    app()