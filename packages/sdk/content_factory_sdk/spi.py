"""
SPI (Service Provider Interface)

定义组件必须实现的接口。
这些接口是稳定的，一旦发布只能加不能改（语义化版本）。
"""

from typing import Any, Protocol, runtime_checkable

from content_factory_core.events import ArticlePublished
from content_factory_core.models import (
    Article,
    Draft,
    RunContext,
    Topic,
)


@runtime_checkable
class DataSourceProvider(Protocol):
    """数据源组件接口"""

    async def fetch_stock_data(self, symbol: str) -> dict[str, Any]:
        """获取股票数据"""
        ...

    async def fetch_news(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """获取新闻"""
        ...

    async def fetch_announcement(self, symbol: str, days: int = 30) -> list[dict[str, Any]]:
        """获取公告"""
        ...


@runtime_checkable
class EditorProvider(Protocol):
    """编辑组件接口"""

    async def draft_article(self, topic: Topic, context: RunContext) -> Draft:
        """根据选题和上下文生成草稿"""
        ...

    def style_fingerprint(self) -> dict[str, Any]:
        """返回编辑的风格指纹"""
        ...

    def can_handle(self, topic: Topic) -> bool:
        """判断是否能处理这个选题（基于偏好）"""
        ...


@runtime_checkable
class ComplianceProvider(Protocol):
    """合规组件接口"""

    async def check(self, draft: Draft) -> dict[str, Any]:
        """
        检查草稿是否合规
        返回: {"passed": bool, "issues": [...], "risk_level": str}
        """
        ...

    async def approve(self, draft: Draft) -> Article:
        """批准草稿，生成终稿"""
        ...


@runtime_checkable
class PublisherProvider(Protocol):
    """
    发布组件接口

    实现可返回 dict 或 ArticlePublished 事件对象。
    推荐实现为返回 ArticlePublished（带 publish_url 属性）。
    """

    async def publish(self, article: Article) -> dict[str, Any] | ArticlePublished:
        """
        发布文章

        返回:
          - dict: {"success": bool, "url": str, "metadata": {...}}
          - ArticlePublished: 事件对象（推荐）
        """
        ...


@runtime_checkable
class ContentGeneratorProvider(Protocol):
    """
    内容生成组件接口（图片 / 视频 / 音乐 / 语音 / 摘要）

    用于接入外部生成式 AI 服务（MiniMax、BibiGPT 等）。
    """

    async def generate(self, prompt: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        生成内容

        返回:
          dict: {
            "type": "image" | "video" | "music" | "speech" | "summary",
            "url": str,              # 生成内容的 URL（可选）
            "content": Any,          # 生成的原始内容
            "metadata": {...}        # 服务返回的元数据
          }
        """
        ...

    def supported_types(self) -> list[str]:
        """返回支持的内容类型列表"""
        ...


@runtime_checkable
class SearchProvider(Protocol):
    """
    专业搜索组件接口

    用于接入专业数据检索服务（dataPro、学术搜索、工商查询等）。
    """

    async def search(self, query: str, domain: str = "general", limit: int = 10) -> dict[str, Any]:
        """
        执行搜索

        Args:
          query: 自然语言查询
          domain: 搜索域 ("general" / "academic" / "business" / "stock" / "risk" / "news")
          limit: 返回条数

        Returns:
          dict: {
            "domain": str,
            "query": str,
            "results": [{"title": str, "content": str, "source": str, "url": str, ...}],
            "total": int,
          }
        """
        ...

    def supported_domains(self) -> list[str]:
        """返回支持的搜索域列表"""
        ...
