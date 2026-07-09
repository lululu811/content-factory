"""
事件总线

组件间通过事件总线通信，实现解耦。
"""

from collections import defaultdict
from collections.abc import Callable
from typing import Any

import structlog
from content_factory_core.events import DomainEvent

logger = structlog.get_logger()

# 事件处理器类型
EventHandler = Callable[[DomainEvent], Any]


class EventBus:
    """事件总线接口"""

    async def emit(self, event: DomainEvent) -> None:
        """发布事件"""
        raise NotImplementedError

    def on(self, event_type: str, handler: EventHandler) -> None:
        """订阅事件"""
        raise NotImplementedError

    async def wait_for(self, event_type: str, timeout: float | None = None) -> DomainEvent:
        """等待特定事件（用于 workflow 人工审批等场景）"""
        raise NotImplementedError


class InMemoryEventBus(EventBus):
    """内存事件总线（测试和单机使用）"""

    def __init__(self) -> None:
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)
        self._event_history: list[DomainEvent] = []

    async def emit(self, event: DomainEvent) -> None:
        """发布事件，同步调用所有处理器"""
        self._event_history.append(event)
        logger.info("event_emitted", event_type=event.event_type, event_id=str(event.event_id))

        handlers = self._handlers.get(event.event_type, [])
        for handler in handlers:
            try:
                await handler(event) if _is_async(handler) else handler(event)
            except Exception as e:
                logger.error(
                    "event_handler_failed",
                    event_type=event.event_type,
                    handler=handler.__name__,
                    error=str(e),
                )

    def on(self, event_type: str, handler: EventHandler) -> None:
        """订阅事件"""
        self._handlers[event_type].append(handler)
        logger.info("event_subscribed", event_type=event_type, handler=handler.__name__)

    async def wait_for(self, event_type: str, timeout: float | None = None) -> DomainEvent:
        """
        等待特定事件
        注意：内存实现不支持真正的等待，只是从历史中查找
        """
        for event in reversed(self._event_history):
            if event.event_type == event_type:
                return event
        raise TimeoutError(f"Event {event_type} not found")

    def get_history(self, event_type: str | None = None) -> list[DomainEvent]:
        """获取事件历史"""
        if event_type:
            return [e for e in self._event_history if e.event_type == event_type]
        return self._event_history.copy()


def _is_async(func: Callable) -> bool:
    """判断函数是否是 async"""
    import inspect

    return inspect.iscoroutinefunction(func)
