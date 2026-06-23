#!/usr/bin/env python3
"""
scripts/filter-candidates.py
过滤候选 feed，从 raw feed JSON 提取出过去 N 天且时长超过一定阈值的视频/音频候选。

用法：
  python3 filter-candidates.py --raw <raw.json> --out <filtered.json> [--days 7] [--min-duration 1200]
"""

import json
import sys
import argparse
from datetime import datetime, timezone, timedelta

def parse_duration(s):
    """将 MM:SS 或 HH:MM:SS 格式的字符串解析为秒数"""
    if not s or ":" not in s:
        return 0
    parts = s.split(":")
    if len(parts) == 2:
        return int(parts[0]) * 60 + int(parts[1])
    elif len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    return 0

def main():
    parser = argparse.ArgumentParser(description="过滤候选 feed")
    parser.add_argument("--raw", required=True, help="原始 feed json 文件路径")
    parser.add_argument("--out", required=True, help="输出过滤后的 json 文件路径")
    parser.add_argument("--days", type=int, default=7, help="时间过滤天数（默认 7 天）")
    parser.add_argument("--min-duration", type=int, default=1200, help="最小音视频时长（秒，默认 1200 秒即 20 分钟）")
    args = parser.parse_args()

    try:
        with open(args.raw, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ 读取原始文件失败: {e}")
        sys.exit(1)

    # 动态计算 N 天前的 UTC 时间戳
    cutoff = (datetime.now(timezone.utc) - timedelta(days=args.days)).strftime('%Y-%m-%dT%H:%M:%SZ')

    filtered = []
    for it in data.get("items", []):
        sec = parse_duration(it.get("duration"))
        pub = it.get("publishedAt", "")
        if sec <= args.min_duration:
            continue
        if pub < cutoff:
            continue
        filtered.append({
            "title": it.get("title"),
            "channelTitle": it.get("channelTitle"),
            "sourceUrl": it.get("sourceUrl"),
            "duration": it.get("duration"),
            "publishedAt": pub,
            "sec": sec,
            "minute": round(sec / 60, 1),
        })

    filtered.sort(key=lambda x: x["publishedAt"], reverse=True)

    try:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(filtered, f, ensure_ascii=False, indent=2)
        print(f"✅ 候选过滤完成: {len(filtered)} 条 → {args.out}")
    except Exception as e:
        print(f"❌ 写入过滤结果失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
