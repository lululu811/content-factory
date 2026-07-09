"""
content-factory-sdk: 平台 SDK

提供 SPI 接口、事件总线、组件注册等平台基础设施。
组件开发者依赖此包来实现自己的组件。
"""

from content_factory_sdk.events import (
    EventBus,
    InMemoryEventBus,
)
from content_factory_sdk.registry import (
    ComponentRegistry,
    discover_components,
)
from content_factory_sdk.spi import (
    ComplianceProvider,
    ContentGeneratorProvider,
    DataSourceProvider,
    EditorProvider,
    PublisherProvider,
    SearchProvider,
)

__version__ = "1.0.0"

__all__ = [
    # SPI
    "DataSourceProvider",
    "EditorProvider",
    "PublisherProvider",
    "ComplianceProvider",
    "ContentGeneratorProvider",
    "SearchProvider",
    # Registry
    "ComponentRegistry",
    "discover_components",
    # Events
    "EventBus",
    "InMemoryEventBus",
]
