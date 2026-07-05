"""End-to-end quickstart example for cninfo-toolkit.

This script demonstrates the full pipeline: query → download → extract.

Usage:
    python examples/quickstart.py

Expected output:
    Found N announcements for 600487.SH
    Downloaded: M, Skipped: 0, Failed: 0
    Extracted: M, Skipped: 0, Failed: 0
    All done! Check ./output/ for results.
"""

from __future__ import annotations

from pathlib import Path

from cninfo_toolkit import (
    download_pdfs,
    extract_pdfs,
    get_announcements,
)


def main() -> None:
    """Run the full pipeline for a single company."""
    ts_code = "600487.SH"  # 亨通光电
    days = 14
    output_dir = Path("./output")

    print(f"=== Querying announcements for {ts_code} (last {days} days) ===")
    anns = get_announcements(ts_code, days=days)
    print(f"Found {len(anns)} announcements")

    if not anns:
        print("No announcements found, exiting.")
        return

    print("\n=== Downloading PDFs ===")
    pdfs_dir = output_dir / "pdfs"
    dl_report = download_pdfs(anns, output_dir=pdfs_dir, skip_existing=True)
    print(f"Downloaded: {dl_report.success_count}")
    print(f"Skipped: {dl_report.skipped_count}")
    print(f"Failed: {dl_report.failed_count}")

    if dl_report.failed_count > 0:
        print("\nFailures:")
        for r in dl_report.results:
            if r.error:
                print(f"  {r.ts_code} {r.ann_date}: {r.error}")

    # Extract from successfully downloaded PDFs
    successful_pdfs = [Path(r.local_path) for r in dl_report.results if r.success]
    if not successful_pdfs:
        print("No PDFs to extract.")
        return

    print("\n=== Extracting text and tables ===")
    extracted_dir = output_dir / "extracted"
    ex_report = extract_pdfs(successful_pdfs, output_dir=extracted_dir, skip_existing=True)
    print(f"Extracted: {ex_report.success_count}")
    print(f"Skipped: {ex_report.skipped_count}")
    print(f"Failed: {ex_report.failed_count}")

    print(f"\n=== Done! Check {output_dir} for results ===")
    print(f"  PDFs: {pdfs_dir}")
    print(f"  Extracted: {extracted_dir}")


if __name__ == "__main__":
    main()