"""
组件注册与发现

通过 Python entry points 机制自动发现已安装的组件。
"""

from importlib.metadata import entry_points
from typing import TypeVar

import structlog

from content_factory_sdk.spi import (
    ComplianceProvider,
    ContentGeneratorProvider,
    DataSourceProvider,
    EditorProvider,
    PublisherProvider,
    SearchProvider,
)

logger = structlog.get_logger()

T = TypeVar("T")

# Entry point groups
ENTRY_POINT_GROUPS = {
    "data_sources": "content_factory.data_sources",
    "editors": "content_factory.editors",
    "compliance": "content_factory.compliance",
    "publishers": "content_factory.publishers",
    "content_generators": "content_factory.content_generators",
    "search_providers": "content_factory.search_providers",
}


class ComponentRegistry:
    """组件注册表"""

    def __init__(self) -> None:
        self._data_sources: dict[str, DataSourceProvider] = {}
        self._editors: dict[str, EditorProvider] = {}
        self._compliance: dict[str, ComplianceProvider] = {}
        self._publishers: dict[str, PublisherProvider] = {}
        self._content_generators: dict[str, ContentGeneratorProvider] = {}
        self._search_providers: dict[str, SearchProvider] = {}

    def register_data_source(self, name: str, provider: DataSourceProvider) -> None:
        """注册数据源组件"""
        self._data_sources[name] = provider
        logger.info("registered_data_source", name=name)

    def register_editor(self, name: str, provider: EditorProvider) -> None:
        """注册编辑组件"""
        self._editors[name] = provider
        logger.info("registered_editor", name=name)

    def register_compliance(self, name: str, provider: ComplianceProvider) -> None:
        """注册合规组件"""
        self._compliance[name] = provider
        logger.info("registered_compliance", name=name)

    def register_publisher(self, name: str, provider: PublisherProvider) -> None:
        """注册发布组件"""
        self._publishers[name] = provider
        logger.info("registered_publisher", name=name)

    def register_content_generator(self, name: str, provider: ContentGeneratorProvider) -> None:
        """注册内容生成组件（图片/视频/音乐/语音）"""
        self._content_generators[name] = provider
        logger.info("registered_content_generator", name=name)

    def register_search_provider(self, name: str, provider: SearchProvider) -> None:
        """注册专业搜索组件（学术/工商/风险/股票）"""
        self._search_providers[name] = provider
        logger.info("registered_search_provider", name=name)

    def get_data_source(self, name: str) -> DataSourceProvider | None:
        """获取数据源"""
        return self._data_sources.get(name)

    def get_editor(self, name: str) -> EditorProvider | None:
        """获取编辑"""
        return self._editors.get(name)

    def get_compliance(self, name: str) -> ComplianceProvider | None:
        """获取合规"""
        return self._compliance.get(name)

    def get_publisher(self, name: str) -> PublisherProvider | None:
        """获取发布"""
        return self._publishers.get(name)

    def get_content_generator(self, name: str) -> ContentGeneratorProvider | None:
        """获取内容生成器"""
        return self._content_generators.get(name)

    def get_search_provider(self, name: str) -> SearchProvider | None:
        """获取专业搜索"""
        return self._search_providers.get(name)

    def list_components(self) -> dict[str, list[str]]:
        """列出所有已注册的组件"""
        return {
            "data_sources": list(self._data_sources.keys()),
            "editors": list(self._editors.keys()),
            "compliance": list(self._compliance.keys()),
            "publishers": list(self._publishers.keys()),
            "content_generators": list(self._content_generators.keys()),
            "search_providers": list(self._search_providers.keys()),
        }


def discover_components(registry: ComponentRegistry | None = None) -> ComponentRegistry:
    """
    自动发现并注册所有已安装的组件

    通过 Python entry points 机制扫描所有 content_factory.* 组的组件。
    """
    if registry is None:
        registry = ComponentRegistry()

    # 发现数据源
    for ep in entry_points(group=ENTRY_POINT_GROUPS["data_sources"]):
        try:
            provider_class = ep.load()
            provider = provider_class()
            registry.register_data_source(ep.name, provider)
        except Exception as e:
            logger.error("failed_to_load_data_source", name=ep.name, error=str(e))

    # 发现编辑
    for ep in entry_points(group=ENTRY_POINT_GROUPS["editors"]):
        try:
            provider_class = ep.load()
            provider = provider_class()
            registry.register_editor(ep.name, provider)
        except Exception as e:
            logger.error("failed_to_load_editor", name=ep.name, error=str(e))

    # 发现合规
    for ep in entry_points(group=ENTRY_POINT_GROUPS["compliance"]):
        try:
            provider_class = ep.load()
            provider = provider_class()
            registry.register_compliance(ep.name, provider)
        except Exception as e:
            logger.error("failed_to_load_compliance", name=ep.name, error=str(e))

    # 发现发布
    for ep in entry_points(group=ENTRY_POINT_GROUPS["publishers"]):
        try:
            provider_class = ep.load()
            provider = provider_class()
            registry.register_publisher(ep.name, provider)
        except Exception as e:
            logger.error("failed_to_load_publisher", name=ep.name, error=str(e))

    # 发现内容生成器
    for ep in entry_points(group=ENTRY_POINT_GROUPS["content_generators"]):
        try:
            provider_class = ep.load()
            provider = provider_class()
            registry.register_content_generator(ep.name, provider)
        except Exception as e:
            logger.error("failed_to_load_content_generator", name=ep.name, error=str(e))

    # 发现专业搜索
    for ep in entry_points(group=ENTRY_POINT_GROUPS["search_providers"]):
        try:
            provider_class = ep.load()
            provider = provider_class()
            registry.register_search_provider(ep.name, provider)
        except Exception as e:
            logger.error("failed_to_load_search_provider", name=ep.name, error=str(e))

    logger.info("components_discovered", summary=registry.list_components())
    return registry
