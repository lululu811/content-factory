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

# 调用 Python 过滤（更稳定，处理 MM:SS 时长 + 时区）
python3 $WORKDIR/scripts/filter-candidates.py --raw "$RAW" --out "$FILTERED" --days 7 --min-duration 1200

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