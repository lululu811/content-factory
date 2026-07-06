"""
选题领域组件

提供选题发现、评分、筛选等功能。
"""

from typing import Any
from uuid import uuid4

from content_factory_core.events import TopicApproved
from content_factory_core.models import RunContext, Topic
from content_factory_sdk.events import EventBus


class TopicProvider:
    """选题提供者"""

    def __init__(self, event_bus: EventBus | None = None) -> None:
        self.event_bus = event_bus

    async def discover_topics(self, context: RunContext) -> list[Topic]:
        """发现候选选题"""
        # Mock 实现：返回一些示例选题
        return [
            Topic(
                tenant_id=context.tenant_id,
                title="稀土行业深度分析",
                description="稀土管制 2.0 政策影响",
                tags=["科技", "新能源"],
                score=85.5,
            ),
            Topic(
                tenant_id=context.tenant_id,
                title="光通信产业链",
                description="CPO 技术突破带来的投资机会",
                tags=["科技"],
                score=78.2,
            ),
        ]

    async def score_topic(self, topic: Topic) -> float:
        """评估选题分数"""
        # Mock 实现：基于标签简单评分
        base_score = 50.0
        if "科技" in topic.tags:
            base_score += 20
        if "新能源" in topic.tags:
            base_score += 15
        return base_score

    async def approve_topic(self, topic: Topic, context: RunContext) -> TopicApproved:
        """批准选题"""
        topic.status = "approved"
        event = TopicApproved(
            tenant_id=context.tenant_id,
            topic_id=topic.id,
        )
        if self.event_bus:
            await self.event_bus.emit(event)
        return event
