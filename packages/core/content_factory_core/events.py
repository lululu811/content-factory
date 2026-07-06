"""
领域事件

定义跨领域通信的事件 schema。
所有事件必须继承 DomainEvent。
"""

from datetime import datetime
from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class DomainEvent(BaseModel):
    """领域事件基类"""
    event_id: UUID = Field(default_factory=uuid4)
    event_type: str
    tenant_id: UUID
    occurred_at: datetime = Field(default_factory=datetime.utcnow)
    payload: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class TopicApproved(DomainEvent):
    """选题已批准"""
    event_type: Literal["topic.approved"] = "topic.approved"
    topic_id: UUID


class ResearchCompleted(DomainEvent):
    """研究完成"""
    event_type: Literal["research.completed"] = "research.completed"
    topic_id: UUID
    research_data: dict[str, Any]


class DraftReady(DomainEvent):
    """草稿就绪"""
    event_type: Literal["draft.ready"] = "draft.ready"
    topic_id: UUID
    editor_id: UUID
    draft_id: UUID


class CompliancePassed(DomainEvent):
    """合规通过"""
    event_type: Literal["compliance.passed"] = "compliance.passed"
    draft_id: UUID
    article_id: UUID


class ArticlePublished(DomainEvent):
    """文章已发布"""
    event_type: Literal["article.published"] = "article.published"
    article_id: UUID
    publish_url: str
