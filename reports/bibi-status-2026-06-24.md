# bibigpt 现状报告 · 2026-06-24 08:04 · 全部

> 自动生成：`scripts/bibi-status-report.py` · 数据源：logs/bibi-calls.jsonl + logs/failed-channels.jsonl

## 1. 整体使用

| 指标 | 数值 |
|---|---|
| 调用次数 | 6 次 |
| 累计扣费 | 120 秒 = 2.0 分钟 |

按命令分布：

| 命令 | 次数 | 累计扣费 (秒) |
|---|---|---|
| `feed` | 3 | 0 |
| `get-subtitle` | 1 | 60 |
| `summarize` | 1 | 60 |
| `me` | 1 | 0 |

## 2. 可用性（get-subtitle + summarize）

| 指标 | 数值 |
|---|---|
| 总调用 | 2 次 |
| `available=true` | 0 次 |
| `available=false` | 2 次 |
| 可用率 | **0.0%** |

### 不可用原因 Top 5

| 原因 | 次数 |
|---|---|
| subtitlesArray 空; rawLang 空; audioUrl 空; playUrl 空; contentText 空 | 1 |
| 包含 fallback 标志: '由于您未提供具体的文字转录稿...' | 1 |

## 3. Hallucination 检测（summarize 专用）

| 指标 | 数值 |
|---|---|
| summarize 调用 | 1 次 |
| `is_hallucination=true` | 1 次 |
| Hallucination 率 | **100.0%** |

### 被检测为 hallucination 的视频

| URL | 原因 |
|---|---|
| https://www.bilibili.com/video/BV1yFj262EzD/ | 包含 fallback 标志: '由于您未提供具体的文字转录稿...' |

## 4. RSS 失败频道

| 频道 | 连续失败天数 | 失败日期 |
|---|---|---|
| 🟢 Acquired - YouTube | 1 | 2026-06-24 |
| 🟢 All-In Podcast - YouTube | 1 | 2026-06-24 |
| 🟢 Bg2 Pod - YouTube | 1 | 2026-06-24 |
| 🟢 巫师财经 | 1 | 2026-06-24 |
| 🟢 张小珺商业访谈录 | 1 | 2026-06-24 |

## 5. 额度消耗（按天）

| 日期 | 调用次数 | 扣费 (秒) | 扣费 (分钟) |
|---|---|---|---|
| 2026-06-23 | 6 | 120 | 2.0 |

## 6. 建议

- ⚠️  **Hallucination 高发** (100%): 1/1 次 summarize 返回 LLM 编造内容 —— 建议所有 summarize 调用都走 bibi-safe.py 检查
- ⚠️  **get-subtitle 可用性低** (0%): 2/2 次返回空字幕 —— 建议加 playwright/yt-dlp 备用字幕抓取方案
