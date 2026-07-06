"""
SPI (Service Provider Interface)

定义组件必须实现的接口。
这些接口是稳定的，一旦发布只能加不能改（语义化版本）。
"""

from typing import Any, Protocol, Union, runtime_checkable

from content_factory_core.events import ArticlePublished
from content_factory_core.models import (
    Article,
    Draft,
    Editor,
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

    async def fetch_announcement(
        self, symbol: str, days: int = 30
    ) -> list[dict[str, Any]]:
        """获取公告"""
        ...


@runtime_checkable
class EditorProvider(Protocol):
    """编辑组件接口"""

    async def draft_article(
        self, topic: Topic, context: RunContext
    ) -> Draft:
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

    async def publish(self, article: Article) -> Union[dict[str, Any], ArticlePublished]:
        """
        发布文章

        返回:
          - dict: {"success": bool, "url": str, "metadata": {...}}
          - ArticlePublished: 事件对象（推荐）
        """
        ...
