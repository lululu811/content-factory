"""
研究提供者

实现研究领域的核心逻辑：数据收集、行业扫描、数据校验。
"""

from typing import Any
from uuid import uuid4

from content_factory_core.events import ResearchCompleted
from content_factory_core.models import RunContext, Topic
from content_factory_sdk.events import EventBus
from content_factory_sdk.spi import DataSourceProvider


class DefaultResearchProvider:
    """默认研究提供者"""

    def __init__(
        self,
        data_sources: list[DataSourceProvider] | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        self.data_sources = data_sources or []
        self.event_bus = event_bus

    async def collect_data(self, topic: Topic, context: RunContext) -> dict[str, Any]:
        """
        收集研究数据
        从所有已注册的数据源收集信息
        """
        research_data: dict[str, Any] = {
            "topic_id": str(topic.id),
            "topic_title": topic.title,
            "sources": [],
            "companies": [],
            "news": [],
            "announcements": [],
        }

        # 从所有数据源收集
        for source in self.data_sources:
            try:
                # 收集新闻
                news = await source.fetch_news(topic.title, limit=10)
                research_data["news"].extend(news)
                research_data["sources"].append(source.__class__.__name__)

                # 如果选题包含股票代码，收集公告
                for tag in topic.tags:
                    if "." in tag:  # 看起来像股票代码
                        announcements = await source.fetch_announcement(tag, days=30)
                        research_data["announcements"].extend(announcements)

            except Exception as e:
                # 记录错误但不中断
                research_data.setdefault("errors", []).append({
                    "source": source.__class__.__name__,
                    "error": str(e),
                })

        return research_data

    async def run_research(self, topic: Topic, context: RunContext) -> ResearchCompleted:
        """
        执行完整研究流程
        返回 ResearchCompleted 事件
        """
        research_data = await self.collect_data(topic, context)

        event = ResearchCompleted(
            tenant_id=context.tenant_id,
            topic_id=topic.id,
            research_data=research_data,
        )

        # 发布事件
        if self.event_bus:
            await self.event_bus.emit(event)

        return event
