"""
RAG 知识库检索适配器

通过 HTTP 客户端调用 workspace/knowledge-base 的 RAG API（api.py），
对内部知识库进行语义检索（hybrid / mmr / vector / bm25）。

服务启动方式（外部项目）:
    cd /Users/chenlei/workspace/knowledge/knowledge-base
    uvicorn api:app --host 127.0.0.1 --port 8002

环境变量:
    CF_KNOWLEDGE_URL - 知识库 API 地址 (默认 http://127.0.0.1:8002)

API 端点:
    POST /retrieve  → {"query": str, "top_k": int, "mode": "hybrid"} → documents[]
    POST /query     → {"query": str, ...} → answer + documents
    GET  /health    → status + document count
"""

from __future__ import annotations

import os
from typing import Any

import httpx
import structlog
from content_factory_sdk.spi import SearchProvider

logger = structlog.get_logger()


class KnowledgeSearchProvider(SearchProvider):
    """RAG 知识库检索（hybrid / mmr / vector / bm25）"""

    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (
            base_url or os.environ.get("CF_KNOWLEDGE_URL", "http://127.0.0.1:8002")
        ).rstrip("/")
        self.is_mock = False
        self._client: httpx.AsyncClient | None = None

    # ---------- SearchProvider SPI ----------

    async def search(self, query: str, domain: str = "internal", limit: int = 10) -> dict[str, Any]:
        """
        检索知识库

        Args:
            query: 自然语言查询
            domain: 搜索模式 (hybrid / mmr / vector / bm25 / internal)
            limit: 返回条数

        Returns:
            {"domain": str, "query": str, "results": [...], "total": int}
        """
        mode = domain if domain in ("hybrid", "mmr", "vector", "bm25") else "hybrid"
        try:
            r = await self._request(
                "POST",
                "/retrieve",
                json={"query": query, "top_k": limit, "mode": mode},
            )
            documents = r.get("documents", [])
            results = [
                {
                    "title": self._extract_title(d.get("source", "")),
                    "content": d.get("content", ""),
                    "source": d.get("source", ""),
                    "score": d.get("score", 0.0),
                    "url": d.get("source", ""),
                }
                for d in documents
            ]
            return {
                "domain": mode,
                "query": query,
                "results": results,
                "total": len(results),
            }
        except Exception as e:
            logger.error("knowledge_search_failed", error=str(e))
            return {
                "domain": mode,
                "query": query,
                "results": [],
                "total": 0,
                "error": str(e),
            }

    def supported_domains(self) -> list[str]:
        return ["internal", "hybrid", "mmr", "vector", "bm25"]

    # ---------- 知识库专属方法 ----------

    async def query_with_answer(
        self, query: str, top_k: int = 5, mode: str = "hybrid"
    ) -> dict[str, Any]:
        """
        检索 + LLM 生成回答（RAG pipeline 完整链路）

        Returns:
            {"answer": str, "documents": [...], "sources": [...]}
        """
        try:
            r = await self._request(
                "POST",
                "/query",
                json={"query": query, "top_k": top_k, "mode": mode},
            )
            return r
        except Exception as e:
            logger.error("knowledge_query_failed", error=str(e))
            return {"answer": "", "documents": [], "error": str(e)}

    async def health(self) -> dict[str, Any]:
        """检查知识库服务状态 + 文档数量"""
        try:
            return await self._request("GET", "/health")
        except Exception as e:
            return {"status": "unreachable", "error": str(e)}

    # ---------- 内部工具 ----------

    async def _request(self, method: str, path: str, **kwargs) -> dict[str, Any]:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(base_url=self.base_url, timeout=30.0)
        try:
            resp = await self._client.request(method, path, **kwargs)
            resp.raise_for_status()
            return resp.json()
        except httpx.ConnectError as e:
            logger.error(
                "knowledge_service_unreachable",
                url=self.base_url,
                hint="请启动知识库 API: cd workspace/knowledge/knowledge-base && uvicorn api:app --port 8002",
            )
            raise RuntimeError(f"无法连接知识库服务 {self.base_url}。请先启动 RAG API。") from e

    @staticmethod
    def _extract_title(source: str) -> str:
        """从 source 路径中提取可读标题"""
        if not source:
            return ""
        # 取最后一段作为标题（去掉扩展名）
        name = source.rstrip("/").split("/")[-1]
        for ext in (".md", ".txt", ".pdf"):
            if name.endswith(ext):
                name = name[: -len(ext)]
                break
        return name
