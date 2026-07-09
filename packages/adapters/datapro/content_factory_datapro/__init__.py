"""
dataPro 专业数据检索适配器

覆盖数据域：
  - 学术文献（CNKI/万方/维普）
  - 企业工商（基础档案/股东/专利）
  - 企业风险（司法/失信/负面舆情）
  - 股票金融（行情/财务/指标）
  - 新闻资讯

环境变量: CF_DATAPRO_TOKEN
"""

import os
from typing import Any

import httpx
import structlog
from content_factory_sdk.spi import SearchProvider

logger = structlog.get_logger()


class DataProSearchProvider(SearchProvider):
    """dataPro 专业搜索"""

    API_BASE = "https://api.datapro.ai/v1"  # 示例 URL，实际按文档调整

    def __init__(
        self,
        token: str | None = None,
        base_url: str | None = None,
    ) -> None:
        self.token = token or os.getenv("CF_DATAPRO_TOKEN")
        if base_url:
            self.API_BASE = base_url
        self._client: httpx.AsyncClient | None = None

        if self.token:
            logger.info("datapro_initialized", has_token=True)
        else:
            logger.warning("datapro_no_token", msg="未设置 CF_DATAPRO_TOKEN，mock 模式")

    @property
    def is_mock(self) -> bool:
        return not self.token

    def supported_domains(self) -> list[str]:
        return ["general", "academic", "business", "risk", "stock", "news"]

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.API_BASE,
                headers={"Authorization": f"Bearer {self.token}"} if self.token else {},
                timeout=30.0,
                trust_env=False,
            )
        return self._client

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    async def search(
        self,
        query: str,
        domain: str = "general",
        limit: int = 10,
    ) -> dict[str, Any]:
        """执行专业搜索"""
        if domain not in self.supported_domains():
            raise ValueError(f"Unsupported domain: {domain}. Supported: {self.supported_domains()}")

        if self.is_mock:
            return {
                "domain": domain,
                "query": query,
                "results": [
                    {
                        "title": f"[Mock] {domain} 结果 {i + 1}: {query}",
                        "content": f"这是关于 {query} 的 mock {domain} 内容",
                        "source": "datapro-mock",
                        "url": f"https://mock.datapro/{domain}/{i}",
                    }
                    for i in range(min(limit, 3))
                ],
                "total": min(limit, 3),
            }

        client = await self._get_client()
        resp = await client.post(
            "/search",
            json={"query": query, "domain": domain, "limit": limit},
        )
        resp.raise_for_status()
        data = resp.json()
        logger.info("datapro_search", domain=domain, query=query[:50], total=data.get("total"))
        return {
            "domain": domain,
            "query": query,
            "results": data.get("results", []),
            "total": data.get("total", 0),
        }

    # ── 便捷方法：按域查询 ──

    async def search_academic(self, query: str, limit: int = 10) -> dict[str, Any]:
        """学术论文检索"""
        return await self.search(query, domain="academic", limit=limit)

    async def search_business(self, company_name: str, limit: int = 10) -> dict[str, Any]:
        """企业工商查询"""
        return await self.search(company_name, domain="business", limit=limit)

    async def search_risk(self, company_name: str, limit: int = 10) -> dict[str, Any]:
        """企业风险查询"""
        return await self.search(company_name, domain="risk", limit=limit)

    async def search_stock(self, query: str, limit: int = 10) -> dict[str, Any]:
        """股票金融查询"""
        return await self.search(query, domain="stock", limit=limit)

    async def search_news(self, query: str, limit: int = 10) -> dict[str, Any]:
        """新闻检索"""
        return await self.search(query, domain="news", limit=limit)
