"""Example: Multi-company batch processing.

This example shows how to query and process announcements for multiple
companies in a single run.

Usage:
    # Prepare a codes.txt file
    echo "600487.SH
300308.SZ
688498.SH" > codes.txt

    # Run the example
    python examples/multi_company.py
"""

from __future__ import annotations

from pathlib import Path

from cninfo_toolkit import (
    batch_query,
    download_pdfs,
    extract_pdfs,
    format_markdown_summary,
)


def main() -> None:
    """Query multiple companies and process all announcements."""
    # Load codes from file
    codes_file = Path("codes.txt")
    if not codes_file.exists():
        print(f"Please create a {codes_file} with one stock code per line.")
        return

    codes = codes_file.read_text(encoding="utf-8").splitlines()
    print(f"=== Querying {len(codes)} companies (last 14 days) ===")
    results = batch_query(codes, days=14)

    total = sum(len(v) for v in results.values())
    print(f"Found {total} announcements total")

    # Show markdown summary
    md = format_markdown_summary(results, title="多公司公告摘要")
    print("\n" + md)

    # Flatten announcements
    all_anns = [ann for anns in results.values() for ann in anns]
    if not all_anns:
        print("No announcements to download.")
        return

    # Download all
    print(f"\n=== Downloading {len(all_anns)} PDFs ===")
    output_dir = Path("./multi-output")
    pdfs_dir = output_dir / "pdfs"
    dl_report = download_pdfs(all_anns, output_dir=pdfs_dir, skip_existing=True)
    print(f"Downloaded: {dl_report.success_count}, Failed: {dl_report.failed_count}")

    # Extract all
    successful = [Path(r.local_path) for r in dl_report.results if r.success]
    if successful:
        print(f"\n=== Extracting {len(successful)} PDFs ===")
        extracted_dir = output_dir / "extracted"
        ex_report = extract_pdfs(successful, output_dir=extracted_dir, skip_existing=True)
        print(f"Extracted: {ex_report.success_count}, Failed: {ex_report.failed_count}")

    print(f"\n=== Done! Check {output_dir} ===")


if __name__ == "__main__":
    main()