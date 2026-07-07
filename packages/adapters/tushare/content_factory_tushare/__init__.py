"""
Tushare 数据源适配器

通过 Tushare API 或 myMCP (xiaodefa.cn) 获取 A 股数据。
需要设置环境变量: CF_TUSHARE_TOKEN 和/或 CF_TUSHARE_BASE_URL
"""

import json
import os
from typing import Any

import httpx
import structlog

from content_factory_sdk.spi import DataSourceProvider

logger = structlog.get_logger()


class TushareDataSource(DataSourceProvider):
    """Tushare 数据源"""

    def __init__(
        self,
        api_token: str | None = None,
        base_url: str | None = None,
    ) -> None:
        self.api_token = api_token or os.getenv("CF_TUSHARE_TOKEN")
        self.base_url = base_url or os.getenv("CF_TUSHARE_BASE_URL")
        self._client = None
        self._http_client: httpx.AsyncClient | None = None

        if self.base_url:
            # 脱敏日志：隐藏真实 token
            safe_url = (
                self.base_url.split("token=")[0] + "token=***"
                if "token=" in self.base_url
                else self.base_url
            )
            logger.info("tushare_using_mymcp", base_url=safe_url)
        elif self.api_token:
            try:
                import tushare as ts

                self._client = ts.pro_api(self.api_token)
                logger.info("tushare_initialized", has_token=True, backend="tushare")
            except ImportError:
                logger.warning("tushare_not_installed", msg="使用 mock 数据")
        else:
            logger.warning(
                "tushare_no_token",
                msg="未设置 CF_TUSHARE_TOKEN 或 CF_TUSHARE_BASE_URL，使用 mock 数据",
            )

    async def _get_http_client(self) -> httpx.AsyncClient:
        """懒初始化 httpx 异步客户端"""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=30.0, trust_env=False)
        return self._http_client

    async def _call_mymcp(self, tool_name: str, arguments: dict) -> Any:
        """调用 myMCP JSON-RPC 接口

        myMCP 是 MCP-over-HTTP 协议，实际使用 JSON-RPC 2.0 格式。
        响应结构: {"result": {"content": [{"type": "text", "text": "{...}"}]}}
        """
        client = await self._get_http_client()
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments},
        }
        resp = await client.post(self.base_url, json=payload)
        resp.raise_for_status()
        data = resp.json()

        # 解析 MCP 响应：提取 content[0].text 中的 JSON
        content = data.get("result", {}).get("content", [])
        if content and content[0].get("type") == "text":
            try:
                return json.loads(content[0]["text"])
            except (json.JSONDecodeError, TypeError):
                return content[0]["text"]
        return data

    async def fetch_stock_data(self, symbol: str) -> dict[str, Any]:
        """获取股票数据"""
        # myMCP 后端
        if self.base_url:
            try:
                result = await self._call_mymcp(
                    "daily",
                    {
                        "ts_code": symbol,
                        "start_date": "20260101",
                        "end_date": "20260707",
                    },
                )
                # myMCP 返回的可能是 list 或 dict
                if isinstance(result, list) and len(result) > 0:
                    latest = result[0]
                    return {
                        "symbol": symbol,
                        "close": float(latest.get("close", 0)),
                        "pct_chg": float(latest.get("pct_chg", 0)),
                        "vol": float(latest.get("vol", 0)),
                        "source": "mymcp",
                    }
                elif isinstance(result, dict) and result.get("items"):
                    latest = result["items"][0]
                    return {
                        "symbol": symbol,
                        "close": float(latest.get("close", 0)),
                        "pct_chg": float(latest.get("pct_chg", 0)),
                        "vol": float(latest.get("vol", 0)),
                        "source": "mymcp",
                    }
            except Exception as e:
                logger.error("mymcp_fetch_failed", symbol=symbol, error=str(e))
        # tushare 后端
        elif self._client:
            try:
                df = self._client.daily(
                    ts_code=symbol, start_date="20260101", end_date="20260707"
                )
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
        # myMCP 后端
        if self.base_url:
            try:
                result = await self._call_mymcp(
                    "news",
                    {
                        "src": "sina",
                        "start_date": "20260701",
                        "end_date": "20260707",
                    },
                )
                if isinstance(result, list) and len(result) > 0:
                    news = []
                    for row in result[:limit]:
                        news.append({
                            "title": row.get("title", ""),
                            "content": row.get("content", ""),
                            "datetime": str(row.get("datetime", "")),
                            "source": "mymcp",
                        })
                    return news
            except Exception as e:
                logger.error("mymcp_news_failed", query=query, error=str(e))
        # tushare 后端
        elif self._client:
            try:
                df = self._client.news(
                    src="sina", start_date="20260701", end_date="20260707"
                )
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
        # myMCP 后端
        if self.base_url:
            try:
                result = await self._call_mymcp(
                    "anns",
                    {
                        "ts_code": symbol,
                        "start_date": "20260101",
                        "end_date": "20260707",
                    },
                )
                if isinstance(result, list) and len(result) > 0:
                    anns = []
                    for row in result[:10]:
                        anns.append({
                            "title": row.get("title", ""),
                            "ann_type": row.get("ann_type", ""),
                            "ann_date": str(row.get("ann_date", "")),
                            "source": "mymcp",
                        })
                    return anns
            except Exception as e:
                logger.error("mymcp_ann_failed", symbol=symbol, error=str(e))
        # tushare 后端
        elif self._client:
            try:
                df = self._client.anns(
                    ts_code=symbol, start_date="20260101", end_date="20260707"
                )
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
