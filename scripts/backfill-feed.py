#!/usr/bin/env python3
"""
scripts/backfill-feed.py
补抓过去 N 天的 feed 数据（不消耗 mark-seen cursor）

用法：
  python3 backfill-feed.py --days 7
  python3 backfill-feed.py --start 2026-06-17 --end 2026-06-24
"""

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

WORKDIR = Path.home() / "content-factory"
RAW_DIR = WORKDIR / "drafts" / "candidates"


def fetch_feed(cursor_iso: str, limit: int = 100) -> dict:
    """调 bibi feed --cursor <ISO> --limit N --json"""
    try:
        result = subprocess.run(
            ["bibi", "feed", "--cursor", cursor_iso, "--limit", str(limit), "--json"],
            capture_output=True, text=True, timeout=60,
        )
        stdout = result.stdout.strip()
        json_start = stdout.find("{")
        if json_start == -1:
            return {"error": "no JSON", "stdout": stdout[:300]}
        return json.loads(stdout[json_start:])
    except subprocess.TimeoutExpired:
        return {"error": "timeout"}
    except Exception as e:
        return {"error": str(e)}


def parse_published_date(iso_str: str) -> str:
    """返回 YYYY-MM-DD"""
    return iso_str[:10]


def main():
    parser = argparse.ArgumentParser(description="补抓过去 N 天的 feed")
    parser.add_argument("--days", type=int, default=7, help="回溯天数（默认 7）")
    parser.add_argument("--start", help="起始日期 YYYY-MM-DD")
    parser.add_argument("--end", help="结束日期 YYYY-MM-DD（默认今天）")
    args = parser.parse_args()

    end_date = datetime.strptime(args.end, "%Y-%m-%d").date() if args.end else datetime.now().date()
    if args.start:
        start_date = datetime.strptime(args.start, "%Y-%m-%d").date()
    else:
        start_date = end_date - timedelta(days=args.days - 1)

    print(f"═══════════════════════════════════════════════════")
    print(f"📡 backfill-feed · {start_date} → {end_date}")
    print(f"═══════════════════════════════════════════════════")

    cursor_iso = f"{start_date}T00:00:00.000Z"

    # 一次性拉 cursor 之后的所有内容
    print(f"\n→ 调用 bibi feed --cursor {cursor_iso} --limit 100")
    feed = fetch_feed(cursor_iso, limit=100)

    if "error" in feed:
        print(f"❌ bibi feed 失败: {feed['error']}")
        sys.exit(1)

    all_items = feed.get("items", [])
    failed = feed.get("failedChannels", [])
    next_cursor = feed.get("nextCursor")

    print(f"  返回: {len(all_items)} 条视频 + {len(failed)} 个失败频道")

    # 按 publishedAt 日期分组
    by_date = {}
    for item in all_items:
        pub_date = parse_published_date(item.get("publishedAt", ""))
        if not pub_date:
            continue
        if pub_date not in by_date:
            by_date[pub_date] = []
        by_date[pub_date].append(item)

    # 给每天写一份 feed-YYYY-MM-DD.json（如果当天已有文件，merge 不覆盖）
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    saved = 0
    for date_str, items in sorted(by_date.items()):
        if date_str > end_date.isoformat():
            continue  # 跳过未来的
        if date_str < start_date.isoformat():
            continue
        path = RAW_DIR / f"feed-{date_str}.json"
        # 读已有（如有），merge
        existing = []
        if path.exists():
            try:
                existing = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                existing = []
        # 去重（按 sourceUrl）
        existing_urls = {it.get("sourceUrl") for it in existing}
        new_items = [it for it in items if it.get("sourceUrl") not in existing_urls]
        merged = existing + new_items
        path.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
        saved += 1
        print(f"  ✅ {date_str}: {len(merged)} 条（+{len(new_items)} 新增）")

    # 写 failed channels 日志
    if failed:
        FAILED_LOG = WORKDIR / "logs" / "failed-channels.jsonl"
        FAILED_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(FAILED_LOG, "a", encoding="utf-8") as f:
            today = datetime.now().date().isoformat()
            record = {"date": today, "failed": failed}
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        print(f"  ⚠️  {len(failed)} 个失败频道 → logs/failed-channels.jsonl")

    print(f"\n📊 总结")
    print(f"  累计日期: {len(by_date)} 天")
    print(f"  累计视频: {len(all_items)} 条")
    print(f"  保存到: {len(by_date)} 个 feed-YYYY-MM-DD.json")
    if next_cursor:
        print(f"  nextCursor: {next_cursor}")


if __name__ == "__main__":
    main()