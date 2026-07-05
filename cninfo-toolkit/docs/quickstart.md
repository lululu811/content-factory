# Quickstart

This guide walks you through the most common use cases in 5 minutes.

## 1. Query announcements for one company

=== "CLI"

    ```bash
    $ cninfo anns 600487.SH
    ## 巨潮公告摘要(14 天)(1 家公司 · 15 条公告)

    ### 600487.SH — 15 条
    - [2026-07-04] 亨通光电关于控股股东部分股权解除质押公告
      - http://static.cninfo.com.cn/finalpage/2026-07-04/1225408156.PDF
    - [2026-07-03] 亨通光电关于2024年限制性股票激励计划第一个解除限售期解除限售暨上市流通的提示性公告
      ...
    ```

=== "Python"

    ```python
    from cninfo_toolkit import get_announcements

    anns = get_announcements("600487.SH", days=14)
    for ann in anns[:3]:
        print(f"[{ann.ann_date}] {ann.title}")
        print(f"  {ann.url}")
    ```

=== "JSON"

    ```bash
    $ cninfo anns 600487.SH --json --output anns.json
    $ cat anns.json | head
    {
      "600487.SH": [
        {
          "ann_id": "1225408156",
          "ts_code": "600487.SH",
          "org_id": "gssh0600487",
          "ann_date": "2026-07-04",
          "title": "亨通光电关于控股股东部分股权解除质押公告",
          "url": "http://static.cninfo.com.cn/finalpage/2026-07-04/1225408156.PDF",
          "sec_code": "600487"
        },
        ...
    ```

## 2. Query multiple companies from a file

=== "CLI"

    ```bash
    # codes.txt: one TS code per line
    $ cat codes.txt
    600487.SH
    300308.SZ
    688498.SH

    $ cninfo anns --code-file codes.txt --days 14 --json --output anns.json
    ```

=== "Python"

    ```python
    from cninfo_toolkit import batch_query

    codes = open("codes.txt").read().splitlines()
    results = batch_query(codes, days=14)

    total = sum(len(v) for v in results.values())
    print(f"Found {total} announcements across {len(results)} companies")
    ```

## 3. Download PDFs

=== "CLI"

    ```bash
    # Download all PDFs from the announcements JSON
    $ cninfo pdf-dl --anns anns.json --output-dir ./pdfs/

    # Download a single PDF
    $ cninfo pdf-dl --url "http://static.cninfo.com.cn/finalpage/2026-06-23/xxx.PDF" \
        --output ./ann.PDF
    ```

=== "Python"

    ```python
    from pathlib import Path
    from cninfo_toolkit import get_announcements, download_pdfs

    anns = get_announcements("600487.SH", days=14)
    report = download_pdfs(anns, output_dir=Path("./pdfs/"))
    print(f"Downloaded: {report.success_count}")
    print(f"Skipped: {report.skipped_count}")
    print(f"Failed: {report.failed_count}")
    ```

## 4. Extract text and tables from PDFs

=== "CLI"

    ```bash
    $ cninfo pdf-extract --pdf-dir ./pdfs/ --output-dir ./extracted/
    ```

=== "Python"

    ```python
    from pathlib import Path
    from cninfo_toolkit import extract_pdfs

    pdfs = list(Path("./pdfs/").glob("*.PDF"))
    report = extract_pdfs(pdfs, output_dir=Path("./extracted/"))
    print(f"Extracted: {report.success_count}")
    ```

## 5. End-to-end pipeline

The `pipeline` command does all three steps in one go:

=== "CLI"

    ```bash
    $ cninfo pipeline 600487.SH 300308.SZ --days 14 --output-dir ./data/

    # After completion, ./data/ contains:
    #   anns-*.json         (announcement metadata)
    #   pdfs/               (downloaded PDFs)
    #     manifest.json     (download report)
    #   extracted/          (extracted JSON)
    ```

=== "Python"

    ```python
    # The `cninfo pipeline` command is the easiest.
    # For programmatic control, call each step separately:
    from pathlib import Path
    from cninfo_toolkit import get_announcements, download_pdfs, extract_pdfs

    anns = get_announcements("600487.SH", days=14)

    dl_report = download_pdfs(anns, output_dir=Path("./pdfs/"))
    successful = [Path(r.local_path) for r in dl_report.results if r.success]

    extract_pdfs(successful, output_dir=Path("./extracted/"))
    ```

## What's next?

- [API Reference](api.md) — Complete API documentation
- [Usage Guide - Query announcements](usage-anns.md) — Deep dive
- [Usage Guide - Download PDFs](usage-pdf-dl.md) — Deep dive
- [Usage Guide - Extract text](usage-pdf-extract.md) — Deep dive
- [Usage Guide - End-to-end pipeline](usage-pipeline.md) — Deep dive