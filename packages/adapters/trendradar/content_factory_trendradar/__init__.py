"""
TrendRadar RSS 热点数据源适配器

直读 TrendRadar 项目的 SQLite 输出数据库（output/rss/YYYY-MM-DD.db），
提供 RSS 条目、订阅源清单、AI 筛选后的热点聚合。

TrendRadar 是一个开源热点助手（v6.10），通过 RSSHub 抓取上百个 RSS 源，
按日期落盘为 SQLite。本适配器直接读取 SQLite，无需 TrendRadar 服务运行。

环境变量:
    CF_TRENDRADAR_DB_DIR - SQLite 目录 (默认 /Users/chenlei/001_project/TrendRadar/output/rss)
"""
from __future__ import annotations

import os
import re
import sqlite3
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import structlog

from content_factory_sdk.spi import DataSourceProvider

logger = structlog.get_logger()

_DEFAULT_DB_DIR = "/Users/chenlei/001_project/TrendRadar/output/rss"


class TrendRadarDataSource(DataSourceProvider):
    """TrendRadar RSS 热点数据源"""

    def __init__(self, db_dir: str | None = None) -> None:
        self.db_dir = Path(
            db_dir or os.environ.get("CF_TRENDRADAR_DB_DIR", _DEFAULT_DB_DIR)
        )
        self.is_mock = not self.db_dir.exists()
        if self.is_mock:
            logger.warning(
                "trendradar_db_missing",
                db_dir=str(self.db_dir),
                hint="请先运行 TrendRadar 抓取 RSS 数据",
            )

    # ---------- DataSourceProvider SPI (兼容接口) ----------

    async def fetch_stock_data(self, symbol: str) -> dict[str, Any]:
        return {"source": "trendradar", "symbol": symbol, "data": []}

    async def fetch_news(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """通过关键词在 RSS 条目中搜索"""
        return await self.search_items(query, limit=limit)

    async def fetch_announcement(
        self, symbol: str, days: int = 30
    ) -> list[dict[str, Any]]:
        return []

    # ---------- TrendRadar 专属方法 ----------

    async def list_sources(self) -> list[dict[str, Any]]:
        """列出所有 RSS 订阅源（从最近 7 天中第一个存在的 DB 读取）"""
        sources = []
        for db_path in self._iter_recent_dbs(days=7):
            conn = self._connect(db_path)
            try:
                cur = conn.execute(
                    "SELECT id, name, feed_url, is_active, item_count, "
                    "last_fetch_status FROM rss_feeds"
                )
                for row in cur.fetchall():
                    sources.append(
                        {
                            "id": row[0],
                            "name": row[1],
                            "feed_url": row[2],
                            "is_active": bool(row[3]),
                            "item_count": row[4],
                            "last_status": row[5],
                            "db": db_path.stem,
                        }
                    )
            finally:
                conn.close()
            break  # 只取第一个（最新）存在的 DB
        return sources

    async def fetch_rss(
        self, feed_id: str, days: int = 1, limit: int = 50
    ) -> list[dict[str, Any]]:
        """获取指定 RSS 源最近 N 天的条目"""
        items = []
        for db_path in self._iter_recent_dbs(days=days):
            conn = self._connect(db_path)
            try:
                cur = conn.execute(
                    "SELECT title, url, summary, author, published_at, feed_id "
                    "FROM rss_items WHERE feed_id = ? ORDER BY published_at DESC LIMIT ?",
                    (feed_id, limit),
                )
                for row in cur.fetchall():
                    items.append(
                        {
                            "title": row[0],
                            "url": row[1],
                            "summary": row[2],
                            "author": row[3],
                            "published_at": row[4],
                            "feed_id": row[5],
                            "db": db_path.stem,
                        }
                    )
            finally:
                conn.close()
        return items

    async def fetch_trending(
        self, topic: str, days: int = 3, limit: int = 20
    ) -> list[dict[str, Any]]:
        """
        AI 风格热点聚合：在多个 RSS 源中按 topic 关键词搜索，
        按相关度（命中次数 × 时间新鲜度）排序，返回热点候选。

        等价于「从上百个 RSS 源里挑出与 topic 相关的一手资料」。
        """
        keywords = self._tokenize(topic)
        if not keywords:
            return []

        # feed_id → 命中条目
        hits: dict[str, list[dict]] = defaultdict(list)
        for db_path in self._iter_recent_dbs(days=days):
            conn = self._connect(db_path)
            try:
                # 粗筛：SQL LIKE 任一关键词
                where = " OR ".join(
                    ["(title LIKE ? OR summary LIKE ?)"] * len(keywords)
                )
                params: list[Any] = []
                for kw in keywords:
                    like = f"%{kw}%"
                    params.extend([like, like])
                sql = (
                    "SELECT title, url, summary, author, published_at, feed_id "
                    f"FROM rss_items WHERE {where} "
                    "ORDER BY published_at DESC"
                )
                cur = conn.execute(sql, params)
                for row in cur.fetchall():
                    item = {
                        "title": row[0],
                        "url": row[1],
                        "summary": row[2] or "",
                        "author": row[3],
                        "published_at": row[4],
                        "feed_id": row[5],
                        "db": db_path.stem,
                    }
                    # 精筛：打分
                    score = self._score(item, keywords)
                    if score > 0:
                        item["score"] = score
                        hits[row[5]].append(item)
            finally:
                conn.close()

        # 展平 + 按 score 排序 + 去重 URL
        all_items = [it for items in hits.values() for it in items]
        seen: set[str] = set()
        unique: list[dict] = []
        for it in sorted(all_items, key=lambda x: x["score"], reverse=True):
            if it["url"] in seen:
                continue
            seen.add(it["url"])
            unique.append(it)
            if len(unique) >= limit:
                break
        return unique

    async def search_items(
        self, keyword: str, days: int = 7, limit: int = 20
    ) -> list[dict[str, Any]]:
        """简单关键词搜索 RSS 条目"""
        items = []
        for db_path in self._iter_recent_dbs(days=days):
            conn = self._connect(db_path)
            try:
                like = f"%{keyword}%"
                cur = conn.execute(
                    "SELECT title, url, summary, published_at, feed_id "
                    "FROM rss_items WHERE title LIKE ? OR summary LIKE ? "
                    "ORDER BY published_at DESC LIMIT ?",
                    (like, like, limit),
                )
                for row in cur.fetchall():
                    items.append(
                        {
                            "title": row[0],
                            "url": row[1],
                            "summary": row[2],
                            "published_at": row[3],
                            "feed_id": row[4],
                            "db": db_path.stem,
                        }
                    )
            finally:
                conn.close()
        return items[:limit]

    async def daily_summary(self, day: date | None = None) -> dict[str, Any]:
        """
        单日 RSS 摘要：按 feed 聚合，返回各源条目数 + top 标题。

        等价于 TrendRadar 的「今日热点日报」。
        """
        day = day or date.today()
        db_path = self.db_dir / f"{day.isoformat()}.db"
        if not db_path.exists():
            return {"date": day.isoformat(), "available": False, "feeds": []}

        conn = self._connect(db_path)
        try:
            by_feed: dict[str, list] = defaultdict(list)
            cur = conn.execute(
                "SELECT title, url, feed_id, published_at FROM rss_items "
                "ORDER BY published_at DESC"
            )
            for row in cur.fetchall():
                by_feed[row[2]].append(
                    {"title": row[0], "url": row[1], "published_at": row[3]}
                )

            feeds_summary = []
            for feed_id, items in by_feed.items():
                feeds_summary.append(
                    {
                        "feed_id": feed_id,
                        "count": len(items),
                        "top_titles": [it["title"] for it in items[:5]],
                    }
                )
            return {
                "date": day.isoformat(),
                "available": True,
                "total_items": sum(len(v) for v in by_feed.values()),
                "feeds": sorted(
                    feeds_summary, key=lambda x: x["count"], reverse=True
                ),
            }
        finally:
            conn.close()

    # ---------- 内部工具 ----------

    def _connect(self, db_path: Path) -> sqlite3.Connection:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _iter_recent_dbs(self, days: int):
        """从今天往前迭代最多 days 个存在的 DB"""
        today = date.today()
        yielded = 0
        for offset in range(days * 2):  # 多扫一些以应对缺失日期
            if yielded >= days:
                return
            d = today - timedelta(days=offset)
            p = self.db_dir / f"{d.isoformat()}.db"
            if p.exists():
                yield p
                yielded += 1

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        """简单分词：中英文分开，去停用词，至少 2 字"""
        # 把非字母数字替换为空格，保留中文
        cleaned = re.sub(r"[^\w一-鿿]", " ", text)
        tokens = [t.strip() for t in cleaned.split() if len(t.strip()) >= 2]
        # 去停用词
        stop = {"的", "了", "和", "与", "是", "在", "我", "有", "也", "被", "把"}
        return [t for t in tokens if t not in stop]

    @staticmethod
    def _score(item: dict, keywords: list[str]) -> float:
        """关键词命中打分：标题 2 倍权重"""
        s = 0.0
        title = item.get("title", "").lower()
        summary = item.get("summary", "").lower()
        for kw in keywords:
            kw = kw.lower()
            if kw in title:
                s += 2.0
            if kw in summary:
                s += 1.0
        # 时间新鲜度加分
        pub = item.get("published_at") or ""
        try:
            dt = datetime.fromisoformat(pub.replace("Z", "+00:00"))
            age_hours = (
                datetime.now(dt.tzinfo) - dt
            ).total_seconds() / 3600 if dt.tzinfo else 0
            if age_hours < 6:
                s += 3.0
            elif age_hours < 24:
                s += 1.5
        except (ValueError, TypeError):
            pass
        return s
