#!/usr/bin/env python3
"""
巨潮资讯网 PDF 下载工具 — 通用工具类

输入:cninfo-anns.py 输出的 JSON 文件(含 ann_id / url / title / date / ts_code)
输出:PDF 文件到指定目录(默认 ./pdfs/)

设计原则:
  - **工具类**:不绑定任何特定项目 / 主题 / 文件布局
  - 输入:任意来源的 anns JSON(anns_d / cninfo-anns.py / 自定义)
  - 输出:由 --output-dir 指定,默认 ./pdfs/(当前目录)
  - 文件名:`{ts_code}_{YYYYMMDD}_{title_slug}.PDF`(扁平,不分 ts_code 子目录)
  - 限速 0.5s/篇 + 重试 3 次 + 指数退避(1/2/4s)
  - PDF 头部校验(必须 `%PDF` magic)
  - 失败日志 → {output-dir}/failed-downloads.json
  - 跳过已下载(--skip-existing 默认开启)

用法:
  # 从 anns.json 下载所有 PDF
  python3 cninfo-pdf-dl.py --anns anns.json --output-dir ./pdfs/

  # 下载单个 PDF(单 URL)
  python3 cninfo-pdf-dl.py --url "http://static.cninfo.com.cn/finalpage/2026-06-23/xxx.PDF" \
    --output ./ann.PDF

  # 限制最多下载 10 篇
  python3 cninfo-pdf-dl.py --anns anns.json --output-dir ./pdfs/ --max 10

依赖:仅 Python 标准库 + curl
"""
import argparse
import json
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def sanitize_filename(title: str, max_len: int = 50) -> str:
    """清洗 title → 安全文件名 slug"""
    slug = re.sub(r'[\\/:\*\?"<>|]', '-', title)
    slug = re.sub(r'\s+', ' ', slug).strip()
    if len(slug) > max_len:
        slug = slug[:max_len].strip()
    slug = slug.strip('. ')
    return slug or "untitled"


def download_pdf(url: str, output_path: Path, retries: int = 3) -> Tuple[bool, Optional[str]]:
    """下载单个 PDF,Returns: (success, error_message)"""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    for attempt in range(1, retries + 1):
        try:
            r = subprocess.run(
                ["curl", "-s", "-L",
                 "-o", str(output_path),
                 "-w", "%{http_code}:%{size_download}",
                 "--max-time", "30",
                 "-H", "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                 "-H", "Referer: http://www.cninfo.com.cn/",
                 url],
                capture_output=True, text=True, timeout=40,
            )
            parts = r.stdout.split(":")
            if len(parts) == 2:
                http_code, size = parts[0], int(parts[1])
            else:
                http_code, size = "?", 0

            if http_code == "200" and size > 1024:
                with open(output_path, "rb") as f:
                    header = f.read(4)
                if header == b"%PDF":
                    return True, None
                else:
                    return False, f"Not a valid PDF (header={header!r})"
            else:
                if attempt < retries:
                    time.sleep(2 ** attempt)
                    continue
                return False, f"HTTP {http_code} / size {size}"
        except subprocess.TimeoutExpired:
            if attempt < retries:
                time.sleep(2 ** attempt)
                continue
            return False, "Timeout (40s)"
        except Exception as e:
            if attempt < retries:
                time.sleep(2 ** attempt)
                continue
            return False, str(e)

    return False, "Max retries exceeded"


def build_pdf_path(output_dir: Path, ts_code: str, ann_date: str, title: str) -> Path:
    """构建 PDF 输出路径(扁平:{ts_code}_{YYYYMMDD}_{slug}.PDF)"""
    slug = sanitize_filename(title)
    date_compact = ann_date.replace("-", "")
    return output_dir / f"{ts_code}_{date_compact}_{slug}.PDF"


def load_anns(json_path: Path) -> Dict[str, List[Dict]]:
    """加载 anns JSON(支持 cninfo-anns.py 输出格式)"""
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)
    # 兼容两种格式:
    # 格式 A:{ts_code: [ann, ann, ...]}  ← cninfo-anns.py 输出
    # 格式 B:[ann, ann, ...](每条含 ts_code 字段)
    if isinstance(data, dict):
        return data
    elif isinstance(data, list):
        result = {}
        for a in data:
            ts = a.get("ts_code", "unknown")
            result.setdefault(ts, []).append(a)
        return result
    else:
        raise ValueError(f"Unsupported anns JSON format: {type(data)}")


def save_failed_log(failed: List[Dict], output_path: Path) -> None:
    """保存失败日志"""
    if failed:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(failed, f, ensure_ascii=False, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description="巨潮资讯网 PDF 下载工具(通用)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--anns",
                        help="anns JSON 文件路径(由 cninfo-anns.py 生成)")
    parser.add_argument("--url",
                        help="单个 PDF URL(单文件下载模式)")
    parser.add_argument("--output",
                        help="单文件下载模式的输出路径")
    parser.add_argument("--output-dir", default="./pdfs",
                        help="批量下载输出目录(默认 ./pdfs/)")
    parser.add_argument("--skip-existing", action="store_true", default=True,
                        help="跳过已下载的 PDF(默认开启)")
    parser.add_argument("--no-skip-existing", dest="skip_existing", action="store_false")
    parser.add_argument("--max", type=int, default=0,
                        help="最多下载多少篇(0=全部,默认 0)")
    parser.add_argument("--rate-limit", type=float, default=0.5,
                        help="限速秒数(默认 0.5s)")
    args = parser.parse_args()

    # ── 单文件模式 ──
    if args.url:
        if not args.output:
            print("❌ --url 模式必须指定 --output")
            sys.exit(1)
        output_path = Path(args.output)
        print(f"⬇️  下载:{args.url}")
        ok, err = download_pdf(args.url, output_path)
        if ok:
            size = output_path.stat().st_size
            print(f"✅ 成功:{output_path}({size//1024} KB)")
            sys.exit(0)
        else:
            print(f"❌ 失败:{err}")
            sys.exit(1)

    # ── 批量模式 ──
    if not args.anns:
        print("❌ 必须指定 --anns 或 --url")
        parser.print_help()
        sys.exit(1)

    anns_path = Path(args.anns)
    if not anns_path.exists():
        print(f"❌ anns JSON 不存在:{anns_path}")
        sys.exit(1)

    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"📂 输出目录:{output_dir}")
    print(f"📄 anns:{anns_path}")
    print()

    data = load_anns(anns_path)

    tasks = []
    for ts_code, anns in data.items():
        for ann in anns:
            tasks.append((ts_code, ann))

    if args.max > 0:
        tasks = tasks[:args.max]

    print(f"📋 待下载:{len(tasks)} 条公告")
    print()

    success_list = []
    failed_list = []
    skipped_list = []

    for i, (ts_code, ann) in enumerate(tasks, 1):
        ann_id = ann.get("ann_id", "")
        ann_date = ann.get("ann_date", "")
        title = ann.get("title", "")
        url = ann.get("url", "")

        if not url:
            failed_list.append({**ann, "error": "empty url"})
            continue

        output_path = build_pdf_path(output_dir, ts_code, ann_date, title)

        if args.skip_existing and output_path.exists():
            size = output_path.stat().st_size
            if size > 1024:
                skipped_list.append({**ann, "local_path": str(output_path), "size_kb": size // 1024})
                print(f"[{i}/{len(tasks)}] {ts_code} {ann_date} ⏭️  已下载({size//1024}KB)")
                continue

        print(f"[{i}/{len(tasks)}] {ts_code} {ann_date} ⬇️  {title[:40]}", end=" ... ")
        ok, err = download_pdf(url, output_path)

        if ok:
            size = output_path.stat().st_size
            print(f"✅ {size//1024}KB")
            success_list.append({**ann, "local_path": str(output_path), "size_kb": size // 1024})
        else:
            print(f"❌ {err}")
            if output_path.exists():
                output_path.unlink()
            failed_list.append({**ann, "error": err})

        if i < len(tasks):
            time.sleep(args.rate_limit)

    print()
    print("=" * 60)
    print(f"📊 下载汇总")
    print(f"  ✅ 成功:{len(success_list)}")
    print(f"  ⏭️  跳过:{len(skipped_list)}")
    print(f"  ❌ 失败:{len(failed_list)}")
    print(f"  📁 总计:{len(tasks)}")

    if failed_list:
        failed_path = output_dir / "failed-downloads.json"
        save_failed_log(failed_list, failed_path)
        print(f"\n⚠️  失败日志:{failed_path}")

    if success_list or skipped_list:
        manifest = {
            "downloaded_at": datetime.now().isoformat(),
            "output_dir": str(output_dir),
            "total_count": len(tasks),
            "success_count": len(success_list),
            "skipped_count": len(skipped_list),
            "failed_count": len(failed_list),
            "files": success_list + skipped_list,
        }
        manifest_path = output_dir / "manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)
        print(f"📋 清单文件:{manifest_path}")


if __name__ == "__main__":
    main()