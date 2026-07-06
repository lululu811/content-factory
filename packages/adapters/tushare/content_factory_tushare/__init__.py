"""
Tushare 数据源适配器

通过 Tushare API 获取 A 股数据。
需要设置环境变量: CF_TUSHARE_TOKEN
"""

import os
from typing import Any

import structlog

from content_factory_sdk.spi import DataSourceProvider

logger = structlog.get_logger()


class TushareDataSource(DataSourceProvider):
    """Tushare 数据源"""

    def __init__(self, api_token: str | None = None) -> None:
        self.api_token = api_token or os.getenv("CF_TUSHARE_TOKEN")
        self._client = None

        if self.api_token:
            try:
                import tushare as ts
                self._client = ts.pro_api(self.api_token)
                logger.info("tushare_initialized", has_token=True)
            except ImportError:
                logger.warning("tushare_not_installed", msg="使用 mock 数据")
        else:
            logger.warning("tushare_no_token", msg="未设置 CF_TUSHARE_TOKEN，使用 mock 数据")

    async def fetch_stock_data(self, symbol: str) -> dict[str, Any]:
        """获取股票数据"""
        if self._client:
            try:
                df = self._client.daily(ts_code=symbol, start_date="20260101", end_date="20260707")
                if not df.empty:
                    latest = df.iloc[0]
                    return {
                        "symbol": symbol,
                        "close": float(latest["close"]),
                        "pct_chg": float(latest["pct_chg"]),
                        "vol": float(latest["vol"]),
                        "source": "tushare",
                    }
            except Exception as e:
                logger.error("tushare_fetch_failed", symbol=symbol, error=str(e))

        # Mock fallback
        return {
            "symbol": symbol,
            "close": 10.5,
            "pct_chg": 1.2,
            "vol": 1000000,
            "source": "mock",
        }

    async def fetch_news(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """获取新闻"""
        if self._client:
            try:
                df = self._client.news(src="sina", start_date="20260701", end_date="20260707")
                if not df.empty:
                    news = []
                    for _, row in df.head(limit).iterrows():
                        news.append({
                            "title": row.get("title", ""),
                            "content": row.get("content", ""),
                            "datetime": str(row.get("datetime", "")),
                            "source": "tushare",
                        })
                    return news
            except Exception as e:
                logger.error("tushare_news_failed", query=query, error=str(e))

        # Mock fallback
        return [
            {
                "title": f"{query} 相关新闻 {i}",
                "content": f"这是关于 {query} 的新闻内容",
                "datetime": "2026-07-07",
                "source": "mock",
            }
            for i in range(min(limit, 3))
        ]

    async def fetch_announcement(
        self, symbol: str, days: int = 30
    ) -> list[dict[str, Any]]:
        """获取公告"""
        if self._client:
            try:
                df = self._client.anns(ts_code=symbol, start_date="20260101", end_date="20260707")
                if not df.empty:
                    anns = []
                    for _, row in df.head(10).iterrows():
                        anns.append({
                            "title": row.get("title", ""),
                            "ann_type": row.get("ann_type", ""),
                            "ann_date": str(row.get("ann_date", "")),
                            "source": "tushare",
                        })
                    return anns
            except Exception as e:
                logger.error("tushare_ann_failed", symbol=symbol, error=str(e))

        # Mock fallback
        return [
            {
                "title": f"{symbol} 公告 {i}",
                "ann_type": "临时公告",
                "ann_date": "2026-07-01",
                "source": "mock",
            }
            for i in range(2)
        ]
