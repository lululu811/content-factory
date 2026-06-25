#!/bin/bash
# scripts/daily-feed.sh
# 每日 bibigpt feed 抓取 + 过滤（v2 · 集成 bibi-safe 防御式包装）
# cron: 0 8 * * * /Users/chenlei/content-factory/scripts/daily-feed.sh

set -e

# 注入 cron 环境变量路径
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$HOME/.local/bin:$PATH"

DATE=$(date +%Y-%m-%d)
WORKDIR=$HOME/content-factory
RAW=$WORKDIR/drafts/candidates/feed-$DATE.json
RAW_META=$WORKDIR/drafts/candidates/feed-$DATE.meta.json
FILTERED=$WORKDIR/drafts/candidates/filtered-$DATE.json
FAILED_LOG=$WORKDIR/logs/failed-channels.jsonl

mkdir -p $WORKDIR/drafts/candidates $WORKDIR/logs

echo "════════════════════════════════════════════════════"
echo "📡 daily-feed · $DATE"
echo "════════════════════════════════════════════════════"

# ─────────────────────────────────────────────
# 1. bibi-safe feed 抓取（防御式包装，捕获 failedChannels）
# ─────────────────────────────────────────────
echo "→ 调用 bibi-safe feed --limit 50"
if ! python3 $WORKDIR/scripts/bibi-safe.py feed --limit 50 > $RAW_META 2>/dev/null; then
    echo "❌ bibi-safe feed 完全失败，退出"
    cat $RAW_META 2>/dev/null
    exit 1
fi

# 提取 items + failedChannels
python3 <<PYEOF
import json
with open("$RAW_META", encoding="utf-8") as f:
    meta = json.load(f)

raw = meta.get("raw", {})
items = raw.get("items", [])
failed = raw.get("failed_channels", [])

# 只保留 items 字段到 RAW
with open("$RAW", "w", encoding="utf-8") as f:
    json.dump({"items": items, "failedChannels": failed}, f, ensure_ascii=False, indent=2)
print(f"  主 feed: {len(items)} 条视频")
print(f"  失败频道: {len(failed)} 个")

if failed:
    for ch in failed:
        print(f"    ⚠️  {ch['title']:30s} | {ch['url'][:60]}")
        print(f"        原因: {ch['message']}")
PYEOF

# ─────────────────────────────────────────────
# 2. 失败频道 → fallback 尝试（yt-dlp，仅当允许时）
# ─────────────────────────────────────────────
if [ -f "$WORKDIR/.config/feed-fallback-enabled" ]; then
    echo ""
    echo "→ 尝试 yt-dlp fallback 失败频道"
    python3 <<PYEOF
import json, subprocess, sys
from datetime import datetime, timezone

with open("$RAW", encoding="utf-8") as f:
    data = json.load(f)
failed = data.get("failedChannels", [])

recovered = []
for ch in failed:
    url = ch["url"]
    title = ch["title"]
    # youtube channel → yt-dlp --flat-playlist
    # bilibili space → yt-dlp --flat-playlist
    if "youtube.com/channel/" in url or "space.bilibili.com" in url:
        try:
            result = subprocess.run(
                ["yt-dlp", url, "--flat-playlist", "--playlist-items", "1-3",
                 "--print", "%(title)s|||%(duration_string)s|||%(url)s",
                 "--no-update", "--no-warnings"],
                capture_output=True, text=True, timeout=20,
            )
            for line in result.stdout.strip().split("\n"):
                if not line or "|||" not in line:
                    continue
                title_v, dur, vid_url = line.split("|||", 2)
                recovered.append({
                    "channelTitle": title,
                    "title": title_v[:200],
                    "duration": dur if dur else "??:??",
                    "sourceUrl": vid_url,
                    "isUnseen": True,
                    "fallback": "yt-dlp",
                })
        except Exception as e:
            print(f"  ❌ {title}: {e}", file=sys.stderr)

if recovered:
    data["items"].extend(recovered)
    with open("$RAW", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  ✅ fallback 找回 {len(recovered)} 条视频")
else:
    print(f"  ⚠️  fallback 无果")
PYEOF
fi

# ─────────────────────────────────────────────
# 3. 记录 failedChannels 到历史日志（连续失败追踪）
# ─────────────────────────────────────────────
python3 <<PYEOF
import json
from datetime import datetime

with open("$RAW", encoding="utf-8") as f:
    data = json.load(f)
failed = data.get("failedChannels", [])
if failed:
    with open("$FAILED_LOG", "a", encoding="utf-8") as f:
        record = {"date": "$DATE", "failed": failed}
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
PYEOF

# ─────────────────────────────────────────────
# 4. 连续失败检测（同一频道连续 3 天失败则告警）
# ─────────────────────────────────────────────
python3 <<PYEOF
import json
from collections import defaultdict
from pathlib import Path

log = Path("$FAILED_LOG")
if not log.exists():
    sys_exit = False
else:
    dates_seen = defaultdict(set)
    with open(log, encoding="utf-8") as f:
        for line in f:
            try:
                rec = json.loads(line)
                for ch in rec.get("failed", []):
                    dates_seen[ch["title"]].add(rec["date"])
            except Exception:
                continue

    streak = []
    for ch_title, dates in dates_seen.items():
        sorted_dates = sorted(dates)
        if len(sorted_dates) >= 3 and sorted_dates[-1] == "$DATE":
            streak.append((ch_title, len(sorted_dates)))

    if streak:
        print("\n⚠️  以下频道已连续 3 天以上 RSS 抓取失败，建议排查：")
        for title, days in streak:
            print(f"    🔴 {title} ({days} 天连续失败)")
PYEOF

# ─────────────────────────────────────────────
# 5. 过滤候选（按时长 + 时间）
# ─────────────────────────────────────────────
echo ""
echo "→ 过滤候选（≥ 20 分钟，过去 7 天）"
python3 $WORKDIR/scripts/filter-candidates.py --raw "$RAW" --out "$FILTERED" --days 7 --min-duration 1200

# ─────────────────────────────────────────────
# 6. 输出 Top 10 候选
# ─────────────────────────────────────────────
echo ""
echo "════════════════════════════════════════════════════"
echo "Top 候选（按时长排序，前 10 条）"
echo "════════════════════════════════════════════════════"
python3 -c "
import json
with open('$FILTERED') as f:
    data = json.load(f)
if not data:
    print('  (空)')
for x in sorted(data, key=lambda x: -x['sec'])[:10]:
    print(f\"  {x['minute']:5.1f}min | {x['channelTitle']:18s} | {x['title'][:80]}\")
"