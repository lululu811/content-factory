"""Command-line interface for cninfo-toolkit.

This module provides the unified `cninfo` CLI with subcommands:
- `cninfo anns`     — query announcement metadata
- `cninfo pdf-dl`   — download announcement PDFs
- `cninfo pdf-extract` — extract text and tables from PDFs
- `cninfo pipeline` — run all three in sequence (convenience command)

After `pip install cninfo-toolkit`, the `cninfo` command is available globally.

Examples:
    $ cninfo anns 600487.SH 300308.SZ --days 14 --json
    $ cninfo pdf-dl --anns anns.json --output-dir ./pdfs/
    $ cninfo pdf-extract --pdf-dir ./pdfs/ --output-dir ./extracted/
    $ cninfo pipeline 600487.SH 300308.SZ --days 14 --output-dir ./data/
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import typer
from rich.console import Console

from content_factory import __version__
from content_factory.cninfo._utils import (
    DEFAULT_RATE_LIMIT_SECONDS,
    is_valid_ts_code,
    parse_ts_code_list,
)
from content_factory.cninfo.anns import (
    Announcement,
    batch_query,
    format_markdown_summary,
    get_announcements,
)
from content_factory.cninfo.pdf_dl import (
    DEFAULT_RETRIES,
    download_pdfs,
)
from content_factory.cninfo.pdf_extract import (
    DEFAULT_MAX_PAGES,
    DEFAULT_SIZE_THRESHOLD_KB,
    extract_pdfs,
)

app = typer.Typer(
    name="cninfo",
    help="Free Python toolkit for cninfo.com.cn (巨潮资讯网) announcements.",
    no_args_is_help=True,
    rich_markup_mode="rich",
    add_completion=False,
)
console = Console()
err_console = Console(stderr=True)


def _version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"cninfo-toolkit {__version__}")
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
    """cninfo-toolkit: Free Python toolkit for cninfo.com.cn announcements."""


# ── anns subcommand ─────────────────────────────────────────────────────────


@app.command("anns")
def anns_cmd(
    ts_codes: list[str] = typer.Argument(
        None,
        help="TS-format stock codes (e.g., 600487.SH 300308.SZ).",
    ),
    code_file: Path | None = typer.Option(
        None,
        "--code-file",
        help="Read stock codes from a file (one per line, or comma-separated).",
    ),
    code_stdin: bool = typer.Option(
        False,
        "--code-stdin",
        help="Read stock codes from stdin.",
    ),
    days: int = typer.Option(14, "--days", "-d", help="Number of days to look back."),
    start: str | None = typer.Option(None, "--start", help="Start date (YYYY-MM-DD)."),
    end: str | None = typer.Option(None, "--end", help="End date (YYYY-MM-DD, default today)."),
    output_json: bool = typer.Option(False, "--json", help="Output JSON instead of Markdown."),
    output_file: Path | None = typer.Option(
        None, "--output", "-o", help="Write to file (default: stdout)."
    ),
) -> None:
    """Query A-share company announcements from cninfo.

    Examples:

        $ cninfo anns 600487.SH

        $ cninfo anns 600487.SH 300308.SZ --days 30 --json

        $ cninfo anns --code-file codes.txt --json --output anns.json

        $ cat codes.txt | cninfo anns --code-stdin --days 14
    """
    codes: list[str] = list(ts_codes or [])
    if code_file:
        codes.extend(parse_ts_code_list(code_file.read_text(encoding="utf-8")))
    if code_stdin:
        codes.extend(parse_ts_code_list(sys.stdin.read()))

    # Dedupe while preserving order
    codes = list(dict.fromkeys(codes))  # Dedupe preserving order

    if not codes:
        err_console.print("[red]Error:[/red] no stock codes provided")
        raise typer.Exit(code=1)

    invalid = [c for c in codes if not is_valid_ts_code(c)]
    if invalid:
        err_console.print(f"[red]Error:[/red] invalid stock codes: {invalid}")
        raise typer.Exit(code=1)

    err_console.print(f"[cyan]Querying {len(codes)} companies, last {days} days...[/cyan]")

    # Query
    if len(codes) == 1:
        anns = get_announcements(
            codes[0],
            days=days,
            start_date=start,
            end_date=end,
        )
        results = {codes[0]: anns}
    else:
        results = batch_query(codes, days=days)

    # Format
    if output_json:
        output_text = json.dumps(
            {ts: [a.to_dict() for a in anns] for ts, anns in results.items()},
            ensure_ascii=False,
            indent=2,
        )
    else:
        output_text = format_markdown_summary(results, title=f"巨潮公告摘要({days} 天)")

    # Output
    if output_file:
        output_file.write_text(output_text, encoding="utf-8")
        err_console.print(f"[green]✅[/green] Written to {output_file} ({len(output_text)} chars)")
    else:
        console.print(output_text)


# ── pdf-dl subcommand ───────────────────────────────────────────────────────


@app.command("pdf-dl")
def pdf_dl_cmd(
    anns_file: Path | None = typer.Option(
        None,
        "--anns",
        help="Announcements JSON file (output of `cninfo anns --json`).",
    ),
    url: str | None = typer.Option(
        None,
        "--url",
        help="Download a single PDF URL (mutually exclusive with --anns).",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Output path for single URL mode.",
    ),
    output_dir: Path = typer.Option(
        Path("./pdfs"),
        "--output-dir",
        help="Output directory for batch mode.",
    ),
    skip_existing: bool = typer.Option(
        True, "--skip-existing/--no-skip-existing", help="Skip existing files."
    ),
    max_downloads: int = typer.Option(0, "--max", help="Max downloads (0=unlimited)."),
    rate_limit: float = typer.Option(
        DEFAULT_RATE_LIMIT_SECONDS, "--rate-limit", help="Seconds between requests."
    ),
    retries: int = typer.Option(DEFAULT_RETRIES, "--retries", help="Retries per file."),
) -> None:
    """Download announcement PDFs.

    Examples:

        $ cninfo pdf-dl --anns anns.json --output-dir ./pdfs/

        $ cninfo pdf-dl --url "http://static.cninfo.com.cn/...PDF" --output ./ann.PDF

        $ cninfo pdf-dl --anns anns.json --output-dir ./pdfs/ --max 10
    """
    # Single URL mode
    if url:
        if not output:
            err_console.print("[red]Error:[/red] --url requires --output")
            raise typer.Exit(code=1)

        from content_factory.cninfo.pdf_dl import download_pdf

        success = download_pdf(url, output, retries=retries)
        if success:
            size_kb = output.stat().st_size // 1024
            err_console.print(f"[green]✅[/green] Downloaded {output} ({size_kb}KB)")
        else:
            err_console.print(f"[red]❌[/red] Failed to download {url}")
            raise typer.Exit(code=1)
        return

    # Batch mode
    if not anns_file:
        err_console.print("[red]Error:[/red] --anns or --url required")
        raise typer.Exit(code=1)

    if not anns_file.exists():
        err_console.print(f"[red]Error:[/red] file not found: {anns_file}")
        raise typer.Exit(code=1)

    data = json.loads(anns_file.read_text(encoding="utf-8"))

    # Normalize: {ts: [ann, ...]} → [ann, ...] (flat)
    anns: list[Announcement] = []
    if isinstance(data, dict):
        for _ts_code, items in data.items():
            for item in items:
                anns.append(Announcement(**item))
    elif isinstance(data, list):
        for item in data:
            anns.append(Announcement(**item))
    else:
        err_console.print("[red]Error:[/red] unsupported JSON format")
        raise typer.Exit(code=1)

    err_console.print(f"[cyan]Downloading {len(anns)} PDFs to {output_dir}...[/cyan]")

    report = download_pdfs(
        anns,
        output_dir=output_dir,
        skip_existing=skip_existing,
        rate_limit=rate_limit,
        retries=retries,
        max_downloads=max_downloads,
    )

    # Save manifest
    manifest = report.to_dict()
    manifest["output_dir"] = str(output_dir)
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    err_console.print(
        f"[green]✅[/green] Done: "
        f"{report.success_count} succeeded, "
        f"{report.skipped_count} skipped, "
        f"{report.failed_count} failed"
    )
    err_console.print(f"[cyan]Manifest:[/cyan] {manifest_path}")


# ── pdf-extract subcommand ──────────────────────────────────────────────────


@app.command("pdf-extract")
def pdf_extract_cmd(
    pdf: Path | None = typer.Option(None, "--pdf", help="Extract a single PDF."),
    pdf_dir: Path | None = typer.Option(None, "--pdf-dir", help="Extract all PDFs in a directory."),
    manifest: Path | None = typer.Option(
        None, "--manifest", help="Use manifest.json from `cninfo pdf-dl`."
    ),
    output_dir: Path = typer.Option(
        Path("./extracted"), "--output-dir", help="Output directory for JSON files."
    ),
    skip_existing: bool = typer.Option(True, "--skip-existing/--no-skip-existing"),
    max_pages: int = typer.Option(DEFAULT_MAX_PAGES, "--max-pages"),
    size_threshold_kb: int = typer.Option(DEFAULT_SIZE_THRESHOLD_KB, "--size-threshold-kb"),
) -> None:
    """Extract text and tables from announcement PDFs.

    Examples:

        $ cninfo pdf-extract --pdf ann.PDF --output-dir ./extracted/

        $ cninfo pdf-extract --pdf-dir ./pdfs/ --output-dir ./extracted/

        $ cninfo pdf-extract --manifest ./pdfs/manifest.json --output-dir ./extracted/
    """
    pdfs: list[Path] = []

    if pdf:
        if not pdf.exists():
            err_console.print(f"[red]Error:[/red] PDF not found: {pdf}")
            raise typer.Exit(code=1)
        pdfs.append(pdf)

    if pdf_dir:
        if not pdf_dir.exists():
            err_console.print(f"[red]Error:[/red] directory not found: {pdf_dir}")
            raise typer.Exit(code=1)
        pdfs.extend(sorted(pdf_dir.glob("*.PDF")))
        pdfs.extend(sorted(pdf_dir.glob("*.pdf")))

    if manifest:
        if not manifest.exists():
            err_console.print(f"[red]Error:[/red] manifest not found: {manifest}")
            raise typer.Exit(code=1)
        manifest_data = json.loads(manifest.read_text(encoding="utf-8"))
        for item in manifest_data.get("results", []):
            local_path = item.get("local_path", "")
            if local_path:
                p = Path(local_path)
                if p.exists():
                    pdfs.append(p)

    if not pdfs:
        err_console.print("[red]Error:[/red] no PDFs found (use --pdf, --pdf-dir, or --manifest)")
        raise typer.Exit(code=1)

    err_console.print(f"[cyan]Extracting {len(pdfs)} PDFs to {output_dir}...[/cyan]")

    report = extract_pdfs(
        pdfs,
        output_dir=output_dir,
        skip_existing=skip_existing,
        max_pages=max_pages,
        size_threshold_kb=size_threshold_kb,
    )

    err_console.print(
        f"[green]✅[/green] Done: "
        f"{report.success_count} succeeded, "
        f"{report.skipped_count} skipped, "
        f"{report.failed_count} failed"
    )


# ── pipeline subcommand (convenience) ───────────────────────────────────────


@app.command("pipeline")
def pipeline_cmd(
    ts_codes: list[str] = typer.Argument(None, help="TS-format stock codes."),
    code_file: Path | None = typer.Option(None, "--code-file"),
    code_stdin: bool = typer.Option(False, "--code-stdin"),
    days: int = typer.Option(14, "--days", "-d"),
    output_dir: Path = typer.Option(
        Path("./cninfo-output"),
        "--output-dir",
        help="Base output directory (will contain anns.json, pdfs/, extracted/).",
    ),
) -> None:
    """Run the full pipeline: query → download → extract.

    Examples:

        $ cninfo pipeline 600487.SH 300308.SZ --days 14 --output-dir ./data/

        $ cninfo pipeline --code-file codes.txt --output-dir ./data/
    """
    # Collect codes
    codes: list[str] = list(ts_codes or [])
    if code_file:
        codes.extend(parse_ts_code_list(code_file.read_text(encoding="utf-8")))
    if code_stdin:
        codes.extend(parse_ts_code_list(sys.stdin.read()))

    codes = list(dict.fromkeys(codes))  # Dedupe preserving order

    if not codes:
        err_console.print("[red]Error:[/red] no stock codes provided")
        raise typer.Exit(code=1)

    invalid = [c for c in codes if not is_valid_ts_code(c)]
    if invalid:
        err_console.print(f"[red]Error:[/red] invalid stock codes: {invalid}")
        raise typer.Exit(code=1)

    output_dir.mkdir(parents=True, exist_ok=True)
    anns_file = output_dir / f"anns-{Path(__file__).stem}.json"
    pdfs_dir = output_dir / "pdfs"
    extracted_dir = output_dir / "extracted"

    # Step 1: Query
    err_console.print("[bold cyan]═══ Step 1/3: Query announcements ═══[/bold cyan]")
    err_console.print(f"[cyan]Querying {len(codes)} companies, last {days} days...[/cyan]")

    if len(codes) == 1:
        anns = get_announcements(codes[0], days=days)
        results = {codes[0]: anns}
    else:
        results = batch_query(codes, days=days)

    anns_file.write_text(
        json.dumps(
            {ts: [a.to_dict() for a in items] for ts, items in results.items()},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    total = sum(len(v) for v in results.values())
    err_console.print(f"[green]✅[/green] {len(results)} companies, {total} announcements")

    # Flatten
    anns_flat: list[Announcement] = [a for items in results.values() for a in items]
    if not anns_flat:
        err_console.print("[yellow]No announcements found, pipeline complete.[/yellow]")
        return

    # Step 2: Download
    err_console.print("[bold cyan]═══ Step 2/3: Download PDFs ═══[/bold cyan]")
    dl_report = download_pdfs(anns_flat, output_dir=pdfs_dir, skip_existing=True)
    err_console.print(
        f"[green]✅[/green] {dl_report.success_count} downloaded, "
        f"{dl_report.skipped_count} skipped, {dl_report.failed_count} failed"
    )

    # Save manifest
    manifest_data = dl_report.to_dict()
    manifest_data["output_dir"] = str(pdfs_dir)
    (pdfs_dir / "manifest.json").write_text(
        json.dumps(manifest_data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # Step 3: Extract
    err_console.print("[bold cyan]═══ Step 3/3: Extract text ═══[/bold cyan]")
    successful_pdfs = [Path(r.local_path) for r in dl_report.results if r.success and r.local_path]
    if successful_pdfs:
        ex_report = extract_pdfs(successful_pdfs, output_dir=extracted_dir, skip_existing=True)
        err_console.print(
            f"[green]✅[/green] {ex_report.success_count} extracted, "
            f"{ex_report.skipped_count} skipped, {ex_report.failed_count} failed"
        )
    else:
        err_console.print("[yellow]No PDFs to extract.[/yellow]")

    err_console.print("[bold green]═══ Pipeline complete ═══[/bold green]")
    err_console.print(f"[cyan]Output:[/cyan] {output_dir}")


if __name__ == "__main__":
    app()
