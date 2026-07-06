"""
content-factory-core: 核心运行时

提供领域模型、事件 schema、配置管理等基础设施。
"""

from content_factory_core.models import (
    Article,
    Draft,
    Editor,
    RunContext,
    Tenant,
    Topic,
)
from content_factory_core.events import (
    DomainEvent,
    TopicApproved,
    ResearchCompleted,
    DraftReady,
)
from content_factory_core.config import Settings

__version__ = "0.3.0"

__all__ = [
    # Models
    "Article",
    "Draft",
    "Editor",
    "RunContext",
    "Tenant",
    "Topic",
    # Events
    "DomainEvent",
    "TopicApproved",
    "ResearchCompleted",
    "DraftReady",
    # Config
    "Settings",
]
