"""
Tushare 数据源适配器

通过 Tushare API 获取 A 股数据。
"""

from typing import Any

from content_factory_sdk.spi import DataSourceProvider


class TushareDataSource(DataSourceProvider):
    """Tushare 数据源"""

    def __init__(self, api_token: str | None = None) -> None:
        self.api_token = api_token
        # 实际使用时会初始化 tushare pro_api
        # import tushare as ts
        # self.pro = ts.pro_api(api_token)

    async def fetch_stock_data(self, symbol: str) -> dict[str, Any]:
        """获取股票数据"""
        # Mock 实现
        return {
            "symbol": symbol,
            "name": f"股票_{symbol}",
            "price": 10.5,
            "pe_ratio": 15.2,
            "pb_ratio": 2.1,
            "market_cap": 100_000_000,
            "industry": "未知",
        }

    async def fetch_news(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """获取新闻"""
        # Mock 实现
        return [
            {
                "title": f"{query} 相关新闻 {i}",
                "source": "tushare",
                "url": f"https://example.com/news/{i}",
                "published_at": "2026-07-07",
            }
            for i in range(min(limit, 3))
        ]

    async def fetch_announcement(
        self, symbol: str, days: int = 30
    ) -> list[dict[str, Any]]:
        """获取公告"""
        # Mock 实现
        return [
            {
                "title": f"{symbol} 公告 {i}",
                "type": "临时公告",
                "date": "2026-07-01",
                "url": f"https://example.com/ann/{i}",
            }
            for i in range(2)
        ]
