"""
写作领域组件

编排编辑组件，生成文章草稿。
"""

from content_factory_core.events import DraftReady
from content_factory_core.models import Draft, RunContext, Topic
from content_factory_sdk.events import EventBus
from content_factory_sdk.registry import ComponentRegistry


class WritingProvider:
    """写作提供者"""

    def __init__(
        self,
        registry: ComponentRegistry | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        self.registry = registry
        self.event_bus = event_bus

    async def write_article(
        self,
        topic: Topic,
        editor_slug: str,
        context: RunContext,
    ) -> Draft:
        """
        根据选题和编辑生成草稿
        """
        if not self.registry:
            raise ValueError("Component registry not initialized")

        editor = self.registry.get_editor(editor_slug)
        if not editor:
            raise ValueError(f"Editor not found: {editor_slug}")

        draft = await editor.draft_article(topic, context)

        # 发布事件
        if self.event_bus:
            event = DraftReady(
                tenant_id=context.tenant_id,
                topic_id=topic.id,
                editor_id=draft.editor_id,
                draft_id=draft.id,
            )
            await self.event_bus.emit(event)

        return draft

    async def select_editor(self, topic: Topic) -> str:
        """
        根据选题选择合适的编辑
        """
        if not self.registry:
            return "yan-su-pai"  # 默认

        # 简单实现：返回第一个能处理这个选题的编辑
        editors = self.registry.list_components().get("editors", [])
        for editor_slug in editors:
            editor = self.registry.get_editor(editor_slug)
            if editor and editor.can_handle(topic):
                return editor_slug

        return editors[0] if editors else "yan-su-pai"
