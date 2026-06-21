#!/bin/bash
# scripts/daily-feed.sh
# 每日 bibigpt feed 抓取 + 过滤
# cron: 0 8 * * * /Users/chenlei/content-factory/scripts/daily-feed.sh

set -e

DATE=$(date +%Y-%m-%d)
WORKDIR=$HOME/content-factory
RAW=$WORKDIR/drafts/candidates/feed-$DATE.json
FILTERED=$WORKDIR/drafts/candidates/filtered-$DATE.json

mkdir -p $WORKDIR/drafts/candidates $WORKDIR/logs

echo "📡 抓取订阅频道..."
bibi feed --limit 50 --json > $RAW 2>> $WORKDIR/logs/feed.log

# 用 Python 过滤（更稳定，处理 MM:SS 时长 + 时区）
python3 - <<EOF
import json
from datetime import datetime, timedelta, timezone

with open("$RAW") as f:
    data = json.load(f)

# 动态算 7 天前的 UTC 时间戳(每天跑自动更新)
# 格式化为 Z 后缀与 bibigpt publishedAt 字段保持一致,避免字符串字典序比较错位
CUTOFF = (datetime.now(timezone.utc) - timedelta(days=7)).strftime('%Y-%m-%dT%H:%M:%SZ')

def parse_duration(s):
    if not s or ":" not in s:
        return 0
    parts = s.split(":")
    if len(parts) == 2:
        return int(parts[0]) * 60 + int(parts[1])
    elif len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    return 0

filtered = []
for it in data.get("items", []):
    sec = parse_duration(it.get("duration"))
    pub = it.get("publishedAt", "")
    if sec <= 1200:  # 20 分钟以下
        continue
    if pub < CUTOFF:
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

with open("$FILTERED", "w") as f:
    json.dump(filtered, f, ensure_ascii=False, indent=2)

print(f"✅ $DATE 候选: {len(filtered)} 条 → $FILTERED")
EOF

# 输出 Top 10 候选（按时长）
echo ""
echo "=== Top 候选（按时长排序）==="
python3 -c "
import json
with open('$FILTERED') as f:
    data = json.load(f)
for x in sorted(data, key=lambda x: -x['sec'])[:10]:
    print(f\"  {x['minute']:5.1f}min | {x['channelTitle']:18s} | {x['title'][:80]}\")
"