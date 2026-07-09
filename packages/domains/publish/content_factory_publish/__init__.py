"""
发布领域组件

提供文章发布到各平台的功能。
"""

from typing import Any

from content_factory_core.events import ArticlePublished
from content_factory_core.models import Article
from content_factory_sdk.events import EventBus


class PublishProvider:
    """发布提供者"""

    def __init__(self, event_bus: EventBus | None = None) -> None:
        self.event_bus = event_bus

    async def publish_to_wechat(self, article: Article) -> dict[str, Any]:
        """发布到微信公众号"""
        # Mock 实现
        return {
            "success": True,
            "url": f"https://mp.weixin.qq.com/s/{article.id}",
            "media_id": f"mock_media_{article.id}",
        }

    async def publish(self, article: Article) -> ArticlePublished:
        """发布文章"""
        result = await self.publish_to_wechat(article)

        event = ArticlePublished(
            tenant_id=article.tenant_id,
            article_id=article.id,
            publish_url=result["url"],
        )

        if self.event_bus:
            await self.event_bus.emit(event)

        return event
