#!/usr/bin/env python3
"""
巨潮资讯网 PDF 解析工具 — 通用工具类

输入:单个 PDF / PDF 目录 / manifest.json(由 cninfo-pdf-dl.py 生成)
输出:extracted JSON 到指定目录(默认 ./extracted/)

设计原则:
  - **工具类**:不绑定任何特定项目 / 主题 / 文件布局
  - 输入灵活:单 PDF / 目录(批量) / manifest.json
  - 输出:由 --output-dir 指定,默认 ./extracted/(当前目录)
  - 文件名:`{pdf_basename}.json`(去掉 .PDF 后缀,加 .json)
  - 大文件保护:> 100KB 触发 max-pages 30 限制,避免 OOM
  - 跳过已抽取(--skip-existing 默认开启)

用法:
  # 单 PDF
  python3 cninfo-pdf-extract.py --pdf ann.PDF --output-dir ./extracted/

  # 目录下所有 PDF(批量)
  python3 cninfo-pdf-extract.py --pdf-dir ./pdfs/ --output-dir ./extracted/

  # 从 manifest.json(推荐,与 cninfo-pdf-dl.py 衔接)
  python3 cninfo-pdf-extract.py --manifest ./pdfs/manifest.json --output-dir ./extracted/

  # 限制大 PDF 最多 30 页
  python3 cninfo-pdf-extract.py --pdf-dir ./pdfs/ --max-pages 30

依赖:pdfplumber(已知可用,见 ~/.mavis/agents/mavis/memory/MEMORY.md)
"""
import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


DEFAULT_SIZE_THRESHOLD_KB = 100
DEFAULT_MAX_PAGES = 30
EXTRACTOR_VERSION = "1.0.0"


def extract_pdf(pdf_path: Path, max_pages: int = DEFAULT_MAX_PAGES,
                size_threshold_kb: int = DEFAULT_SIZE_THRESHOLD_KB) -> Dict:
    """
    解析 PDF → {full_text, tables, page_count, truncated}

    max_pages: 最多抽取的页数(避免大文件 OOM)
    size_threshold_kb: 超过这个大小就触发 max_pages 限制
    """
    import pdfplumber

    file_size_kb = pdf_path.stat().st_size / 1024
    truncated = False

    if file_size_kb > size_threshold_kb:
        actual_max_pages = max_pages
        truncated = True
    else:
        actual_max_pages = 9999

    full_text_parts = []
    tables = []
    page_count = 0

    try:
        with pdfplumber.open(str(pdf_path)) as pdf:
            page_count = len(pdf.pages)
            pages_to_process = min(page_count, actual_max_pages)

            for i in range(pages_to_process):
                page = pdf.pages[i]

                text = page.extract_text() or ""
                if text:
                    full_text_parts.append(f"=== Page {i+1} ===\n{text}")

                page_tables = page.extract_tables()
                for t in page_tables:
                    if t:
                        tables.append({
                            "page": i + 1,
                            "rows": [[cell.strip() if cell else "" for cell in row] for row in t]
                        })

    except Exception as e:
        return {
            "error": str(e),
            "error_type": type(e).__name__,
        }

    return {
        "full_text": "\n\n".join(full_text_parts),
        "tables": tables,
        "page_count": page_count,
        "pages_processed": pages_to_process,
        "truncated": truncated,
        "file_size_kb": round(file_size_kb, 2),
    }


def build_output_path(output_dir: Path, pdf_path: Path) -> Path:
    """构建 extracted JSON 输出路径:{output_dir}/{pdf_stem}.json"""
    return output_dir / f"{pdf_path.stem}.json"


def process_pdf(pdf_path: Path, output_path: Path,
                max_pages: int, size_threshold_kb: int,
                skip_existing: bool = True) -> Tuple[bool, Optional[str]]:
    """处理单个 PDF,返回 (success, error_message)"""

    if skip_existing and output_path.exists():
        return True, "skipped (existing)"

    if not pdf_path.exists():
        return False, f"PDF 不存在:{pdf_path}"

    result = extract_pdf(pdf_path, max_pages, size_threshold_kb)

    if "error" in result:
        return False, f"{result['error_type']}: {result['error']}"

    output = {
        "pdf_path": str(pdf_path),
        "extracted_at": datetime.now().isoformat(),
        "extractor_version": EXTRACTOR_VERSION,
        "page_count": result["page_count"],
        "pages_processed": result["pages_processed"],
        "truncated": result["truncated"],
        "file_size_kb": result["file_size_kb"],
        "full_text": result["full_text"],
        "tables": result["tables"],
        "table_count": len(result["tables"]),
    }

    # 如果 manifest 含 ann_id / ts_code / ann_date / title,合并到输出
    # (由 caller 通过 output dict 传递)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    return True, None


def main():
    parser = argparse.ArgumentParser(
        description="巨潮资讯网 PDF 解析工具(通用)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--pdf",
                        help="单个 PDF 文件路径")
    parser.add_argument("--pdf-dir",
                        help="PDF 目录路径(批量解析目录下所有 .PDF / .pdf)")
    parser.add_argument("--manifest",
                        help="manifest.json 文件路径(cninfo-pdf-dl.py 输出,推荐)")
    parser.add_argument("--output-dir", default="./extracted",
                        help="extracted JSON 输出目录(默认 ./extracted/)")
    parser.add_argument("--max-pages", type=int, default=DEFAULT_MAX_PAGES,
                        help=f"大 PDF 最多解析页数(默认 {DEFAULT_MAX_PAGES})")
    parser.add_argument("--size-threshold-kb", type=int, default=DEFAULT_SIZE_THRESHOLD_KB,
                        help=f"触发 max-pages 的文件大小阈值 KB(默认 {DEFAULT_SIZE_THRESHOLD_KB})")
    parser.add_argument("--skip-existing", action="store_true", default=True,
                        help="跳过已抽取(默认开启)")
    parser.add_argument("--no-skip-existing", dest="skip_existing", action="store_false")
    args = parser.parse_args()

    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    tasks = []  # (pdf_path, output_path, metadata)

    # ── 单 PDF 模式 ──
    if args.pdf:
        pdf_path = Path(args.pdf)
        if not pdf_path.exists():
            print(f"❌ PDF 不存在:{pdf_path}")
            sys.exit(1)
        output_path = build_output_path(output_dir, pdf_path)
        tasks.append((pdf_path, output_path, {}))

    # ── 目录批量模式 ──
    elif args.pdf_dir:
        pdf_dir = Path(args.pdf_dir)
        if not pdf_dir.exists():
            print(f"❌ PDF 目录不存在:{pdf_dir}")
            sys.exit(1)
        for pdf_path in sorted(pdf_dir.glob("*.PDF")) + sorted(pdf_dir.glob("*.pdf")):
            output_path = build_output_path(output_dir, pdf_path)
            tasks.append((pdf_path, output_path, {}))

    # ── manifest 模式(推荐)──
    elif args.manifest:
        manifest_path = Path(args.manifest)
        if not manifest_path.exists():
            print(f"❌ manifest 不存在:{manifest_path}")
            sys.exit(1)
        with open(manifest_path, encoding="utf-8") as f:
            manifest = json.load(f)
        for file_info in manifest.get("files", []):
            pdf_path = Path(file_info.get("local_path", ""))
            if not pdf_path.exists():
                continue
            output_path = build_output_path(output_dir, pdf_path)
            # 把 ann 元数据传过去,合并到 extracted JSON
            metadata = {
                "ann_id": file_info.get("ann_id"),
                "ts_code": file_info.get("ts_code"),
                "ann_date": file_info.get("ann_date"),
                "title": file_info.get("title"),
            }
            tasks.append((pdf_path, output_path, metadata))

    else:
        parser.print_help()
        sys.exit(1)

    print(f"📂 输出目录:{output_dir}")
    print(f"📋 待解析:{len(tasks)} 个 PDF")
    print()

    success_count = 0
    skipped_count = 0
    failed_count = 0
    failed_list = []

    for i, (pdf_path, output_path, metadata) in enumerate(tasks, 1):
        # 跳过已抽取
        if args.skip_existing and output_path.exists():
            skipped_count += 1
            print(f"[{i}/{len(tasks)}] {pdf_path.name} ⏭️  已抽取")
            continue

        size_kb = pdf_path.stat().st_size / 1024
        print(f"[{i}/{len(tasks)}] {pdf_path.name} ({size_kb:.1f}KB) ... ", end="")

        ok, err = process_pdf(
            pdf_path, output_path, args.max_pages, args.size_threshold_kb,
            args.skip_existing,
        )

        # 合并 metadata 到 extracted JSON
        if ok and err != "skipped (existing)" and metadata:
            try:
                with open(output_path, encoding="utf-8") as f:
                    data = json.load(f)
                data.update(metadata)
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"⚠️  metadata 合并失败:{e}")

        if err == "skipped (existing)":
            skipped_count += 1
            print("⏭️  跳过")
        elif ok:
            success_count += 1
            try:
                with open(output_path, encoding="utf-8") as f:
                    data = json.load(f)
                pc = data.get("page_count", "?")
                tc = data.get("table_count", 0)
                trunc = " [截断]" if data.get("truncated") else ""
                print(f"✅ {pc} 页 / {tc} 表格{trunc}")
            except Exception:
                print("✅")
        else:
            failed_count += 1
            failed_list.append({"pdf": str(pdf_path), "error": err})
            print(f"❌ {err}")

        if i < len(tasks):
            time.sleep(0.3)

    print()
    print("=" * 60)
    print(f"📊 解析汇总")
    print(f"  ✅ 成功:{success_count}")
    print(f"  ⏭️  跳过:{skipped_count}")
    print(f"  ❌ 失败:{failed_count}")
    print(f"  📁 总计:{len(tasks)}")

    if failed_list:
        failed_path = output_dir / "failed-extracts.json"
        failed_path.parent.mkdir(parents=True, exist_ok=True)
        with open(failed_path, "w", encoding="utf-8") as f:
            json.dump(failed_list, f, ensure_ascii=False, indent=2)
        print(f"\n⚠️  失败日志:{failed_path}")


if __name__ == "__main__":
    main()