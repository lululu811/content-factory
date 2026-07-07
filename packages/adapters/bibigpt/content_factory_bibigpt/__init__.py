"""
BibiGPT 数据源适配器

通过 BibiGPT API 把任意视频/音频 URL 转为结构化摘要、完整字幕、思维导图。
需要环境变量: CF_BIBIGPT_TOKEN

OpenAPI: https://bibigpt.co/api/openapi.json
Base URL: https://api.bibigpt.co/api
"""
import os
from typing import Any

import httpx
import structlog

from content_factory_sdk.spi import DataSourceProvider

logger = structlog.get_logger()


class BibiGPTDataSource(DataSourceProvider):
    """BibiGPT 视频/音频摘要数据源"""

    API_BASE = "https://api.bibigpt.co/api"

    def __init__(self, token: str | None = None) -> None:
        self.token = token or os.getenv("CF_BIBIGPT_TOKEN")
        self._client: httpx.AsyncClient | None = None

        if self.token:
            logger.info("bibigpt_initialized", has_token=True)
        else:
            logger.warning("bibigpt_no_token", msg="未设置 CF_BIBIGPT_TOKEN，使用 mock 模式")

    @property
    def is_mock(self) -> bool:
        return not self.token

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.API_BASE,
                headers={"Authorization": f"Bearer {self.token}" if self.token else ""},
                timeout=60.0,
                trust_env=False,
            )
        return self._client

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    async def summarize_video(self, url: str) -> dict[str, Any]:
        """
        提交视频/音频 URL 获取摘要

        返回:
            {"task_id": str, "status": str, "summary": str, "transcript": str, ...}
        """
        if self.is_mock:
            return {
                "task_id": "mock-task-id",
                "status": "completed",
                "summary": f"[Mock] {url} 的结构化摘要",
                "transcript": "[Mock] 完整字幕内容...",
                "source": "bibigpt-mock",
            }

        client = await self._get_client()
        resp = await client.post("/summary", json={"url": url})
        resp.raise_for_status()
        data = resp.json()
        logger.info("bibigpt_summarize", url=url, task_id=data.get("task_id"))
        return data

    async def get_task_status(self, task_id: str) -> dict[str, Any]:
        """查询任务状态"""
        if self.is_mock:
            return {"task_id": task_id, "status": "completed"}

        client = await self._get_client()
        resp = await client.get(f"/task/{task_id}")
        resp.raise_for_status()
        return resp.json()

    # ── DataSourceProvider SPI 实现（BibiGPT 作为辅助数据源） ──

    async def fetch_stock_data(self, symbol: str) -> dict[str, Any]:
        """BibiGPT 不提供股票数据"""
        return {"symbol": symbol, "source": "bibigpt", "info": "BibiGPT 专注音视频摘要"}

    async def fetch_news(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """BibiGPT 不提供新闻"""
        return []

    async def fetch_announcement(self, symbol: str, days: int = 30) -> list[dict[str, Any]]:
        """BibiGPT 不提供公告"""
        return []
