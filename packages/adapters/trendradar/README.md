# TrendRadar RSS 热点适配器 (content-factory-trendradar)

直读 TrendRadar 项目的 SQLite 输出（`output/rss/YYYY-MM-DD.db`），提供 RSS 条目、订阅源清单、AI 风格热点聚合。

## 前置依赖

TrendRadar 项目（`/Users/chenlei/001_project/TrendRadar`）需要先运行一次数据抓取，生成本地 SQLite。

## 环境变量

| 变量名 | 必需 | 说明 |
|---|---|---|
| `CF_TRENDRADAR_DB_DIR` | 否 | SQLite 目录，默认 `/Users/chenlei/001_project/TrendRadar/output/rss` |

## 用法

```python
from content_factory_trendradar import TrendRadarDataSource

tr = TrendRadarDataSource()

# 订阅源清单
sources = await tr.list_sources()

# AI 热点聚合：从 RSS 中挑出与 topic 相关的条目
hits = await tr.fetch_trending("AI Agent 行业", days=3, limit=20)

# 单源最近 N 天
items = await tr.fetch_rss("cls-telegraph", days=1)

# 单日摘要（类似 TrendRadar 日报）
summary = await tr.daily_summary()
```
