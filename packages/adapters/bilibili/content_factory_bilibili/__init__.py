"""
B站一手资料数据源适配器

通过 HTTP 客户端调用本地 bilibili_toolkit FastAPI 服务（bilibili_toolkit.server:app），
获取字幕、弹幕、UP主动态、充电问答等一手素材。

服务启动方式（外部项目）:
    cd /Users/chenlei/002_tools/bilibili-subtitle-downloader
    uvicorn bilibili_toolkit.server:app --host 127.0.0.1 --port 8100

环境变量:
    CF_BILIBILI_URL      - bilibili_toolkit 服务地址 (默认 http://127.0.0.1:8100)
    CF_BILIBILI_API_KEY  - 可选，B站 API Key（对应服务端的 BILIBILI_API_KEY）

注意: 字幕/弹幕下载为异步任务，本适配器会自动轮询任务状态。
"""

from __future__ import annotations

import asyncio
import os
from typing import Any

import httpx
import structlog
from content_factory_sdk.spi import DataSourceProvider

logger = structlog.get_logger()


class BilibiliDataSource(DataSourceProvider):
    """B站一手资料数据源（字幕/弹幕/动态/充电问答）"""

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        task_poll_interval: float = 1.0,
        task_timeout: float = 60.0,
    ) -> None:
        self.base_url = (
            base_url or os.environ.get("CF_BILIBILI_URL", "http://127.0.0.1:8100")
        ).rstrip("/")
        self.api_key = api_key or os.environ.get("CF_BILIBILI_API_KEY")
        self.task_poll_interval = task_poll_interval
        self.task_timeout = task_timeout
        self.is_mock = False
        self._client: httpx.AsyncClient | None = None

    # ---------- DataSourceProvider SPI (兼容接口) ----------

    async def fetch_stock_data(self, symbol: str) -> dict[str, Any]:
        """B站不支持股票代码查询，返回空"""
        return {"source": "bilibili", "symbol": symbol, "data": []}

    async def fetch_news(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """通过关键词搜索UP主动态，作为「新闻」近似"""
        try:
            # B站工具没有关键词搜索，退化为空
            logger.warning("bilibili_no_keyword_search", query=query)
            return []
        except Exception as e:
            logger.error("bilibili_fetch_news_failed", error=str(e))
            return []

    async def fetch_announcement(self, symbol: str, days: int = 30) -> list[dict[str, Any]]:
        """B站不支持公告查询"""
        return []

    # ---------- B站专属方法 ----------

    async def fetch_video_subtitle(self, bvid_or_url: str, lang: str = "zh-CN") -> dict[str, Any]:
        """
        获取视频字幕 markdown

        Args:
            bvid_or_url: BV号 或 视频 URL (e.g. "BV1xx..." 或 "https://www.bilibili.com/video/BV1xx")
            lang: 语言 (zh-CN / en / ...)

        Returns:
            {"bvid": str, "markdown": str, "task_id": str, "status": "completed"}
        """
        task_id = await self._post_task(
            "/api/subtitles",
            {"url": self._normalize_video_url(bvid_or_url), "lang": lang},
        )
        result = await self._poll_task(task_id)
        result["bvid"] = self._extract_bvid(bvid_or_url)
        return result

    async def fetch_danmaku(self, bvid_or_url: str, segment_index: int = 1) -> dict[str, Any]:
        """
        获取视频弹幕

        Returns:
            {"bvid": str, "danmaku": list, "total": int}
        """
        task_id = await self._post_task(
            "/api/danmaku",
            {"url": self._normalize_video_url(bvid_or_url), "segment_index": segment_index},
        )
        result = await self._poll_task(task_id)
        result["bvid"] = self._extract_bvid(bvid_or_url)
        return result

    async def fetch_up_dynamics(self, uid: str, download_images: bool = False) -> dict[str, Any]:
        """
        获取 UP主动态（同步 API，无需轮询）

        Returns:
            {"uid": str, "dynamics": list, "total": int}
        """
        r = await self._request(
            "GET", f"/api/dynamics/{uid}", params={"download_images": download_images}
        )
        return {"uid": uid, **r}

    async def fetch_qa(self, uid: str, page: int = 1) -> dict[str, Any]:
        """
        获取 UP主充电问答（同步 API）

        Returns:
            {"uid": str, "page": int, "qa_list": list}
        """
        r = await self._request("GET", f"/api/charging/{uid}", params={"page": page})
        return {"uid": uid, "page": page, **r}

    async def fetch_space_videos(self, uid: str) -> dict[str, Any]:
        """获取 UP主空间视频列表"""
        r = await self._request("GET", f"/api/space/{uid}")
        return {"uid": uid, **r}

    # ---------- 内部工具 ----------

    async def _request(self, method: str, path: str, **kwargs) -> dict[str, Any]:
        if self._client is None or self._client.is_closed:
            headers = {}
            if self.api_key:
                headers["X-API-Key"] = self.api_key
            self._client = httpx.AsyncClient(base_url=self.base_url, timeout=30.0, headers=headers)
        try:
            resp = await self._client.request(method, path, **kwargs)
            resp.raise_for_status()
            return resp.json()
        except httpx.ConnectError as e:
            logger.error(
                "bilibili_service_unreachable",
                url=self.base_url,
                hint="请启动 bilibili_toolkit 服务: uvicorn bilibili_toolkit.server:app --port 8100",
            )
            raise RuntimeError(
                f"无法连接 B站服务 {self.base_url}。请先启动 bilibili_toolkit 服务。"
            ) from e

    async def _post_task(self, path: str, payload: dict) -> str:
        """提交异步任务，返回 task_id"""
        r = await self._request("POST", path, json=payload)
        return r.get("task_id") or r["id"]

    async def _poll_task(self, task_id: str) -> dict[str, Any]:
        """轮询任务状态直到完成"""
        deadline = asyncio.get_event_loop().time() + self.task_timeout
        while True:
            r = await self._request("GET", f"/api/task/{task_id}")
            status = r.get("status", "").lower()
            if status in ("completed", "done", "success", "finished"):
                return r
            if status in ("failed", "error"):
                raise RuntimeError(f"任务失败: {r.get('error', 'unknown')}")
            if asyncio.get_event_loop().time() > deadline:
                raise TimeoutError(f"任务超时 ({self.task_timeout}s): {task_id}")
            await asyncio.sleep(self.task_poll_interval)

    @staticmethod
    def _normalize_video_url(bvid_or_url: str) -> str:
        if bvid_or_url.startswith("http"):
            return bvid_or_url
        # 纯 BV 号
        if bvid_or_url.upper().startswith("BV"):
            return f"https://www.bilibili.com/video/{bvid_or_url}"
        return bvid_or_url

    @staticmethod
    def _extract_bvid(bvid_or_url: str) -> str:
        if bvid_or_url.upper().startswith("BV"):
            return bvid_or_url.split("?")[0]
        # 从 URL 中提取
        for part in bvid_or_url.rstrip("/").split("/"):
            if part.upper().startswith("BV"):
                return part.split("?")[0]
        return bvid_or_url
