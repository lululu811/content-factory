"""
CNInfo 数据源适配器

通过巨潮资讯网 API 获取上市公司公告。
"""

import os
from typing import Any

import structlog

from content_factory_sdk.spi import DataSourceProvider

logger = structlog.get_logger()


class CninfoDataSource(DataSourceProvider):
    """巨潮资讯数据源"""

    def __init__(self) -> None:
        self.base_url = "http://www.cninfo.com.cn/api"
        logger.info("cninfo_initialized")

    async def fetch_stock_data(self, symbol: str) -> dict[str, Any]:
        """获取股票数据（巨潮不提供行情，返回基础信息）"""
        return {
            "symbol": symbol,
            "source": "cninfo",
            "info_url": f"http://www.cninfo.com.cn/new/disclosure/stock?orgId=9900000000&stockCode={symbol}",
        }

    async def fetch_news(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """巨潮不提供新闻，返回空"""
        return []

    async def fetch_announcement(
        self, symbol: str, days: int = 30
    ) -> list[dict[str, Any]]:
        """获取公告"""
        # 实际实现需要调用巨潮 API
        # 这里提供 mock 实现
        logger.info("cninfo_fetch_announcements", symbol=symbol, days=days)

        return [
            {
                "title": f"{symbol} 公告 - 年度报告",
                "type": "定期报告",
                "date": "2026-04-30",
                "url": f"http://www.cninfo.com.cn/new/disclosure/detail?stockCode={symbol}&announcementId=123",
                "source": "cninfo",
            },
            {
                "title": f"{symbol} 公告 - 董事会决议",
                "type": "临时公告",
                "date": "2026-06-15",
                "url": f"http://www.cninfo.com.cn/new/disclosure/detail?stockCode={symbol}&announcementId=124",
                "source": "cninfo",
            },
        ]
