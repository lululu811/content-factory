"""
A/B 测试与数据回流

支持多编辑并行产出和风格选择。
"""

from uuid import UUID

import structlog
from content_factory_core.models import Editor, RunContext, Topic

from content_factory_sdk import EventBus
from content_factory_sdk.registry import ComponentRegistry

logger = structlog.get_logger()


class StyleFingerprint:
    """编辑风格指纹"""

    def __init__(self, formality: float, risk_tolerance: float, vocabulary: list[str]):
        self.formality = formality
        self.risk_tolerance = risk_tolerance
        self.vocabulary = vocabulary

    def distance_to(self, topic_preference: dict) -> float:
        """计算与话题偏好的距离（越小越匹配）"""
        formality_diff = abs(self.formality - topic_preference.get("formality", 0.5))
        risk_diff = abs(self.risk_tolerance - topic_preference.get("risk_tolerance", 0.5))
        return formality_diff + risk_diff

    def to_dict(self) -> dict:
        return {
            "formality": self.formality,
            "risk_tolerance": self.risk_tolerance,
            "vocabulary": self.vocabulary,
        }


def extract_fingerprint(editor: Editor) -> StyleFingerprint:
    """从编辑器配置中提取风格指纹"""
    config = editor.config
    return StyleFingerprint(
        formality=config.get("formality", 0.5),
        risk_tolerance=config.get("risk_tolerance", 0.5),
        vocabulary=config.get("keywords", []),
    )


def match_editor_for_topic(
    topic: Topic,
    editors: list[Editor],
    preference: dict | None = None,
) -> list[tuple[Editor, float]]:
    """为话题匹配最佳编辑（按匹配度排序）"""
    preference = preference or {}
    matches = []
    for editor in editors:
        fingerprint = extract_fingerprint(editor)
        distance = fingerprint.distance_to(preference)
        matches.append((editor, distance))

    matches.sort(key=lambda x: x[1])
    return matches


async def parallel_draft(
    topic: Topic,
    editor_slugs: list[str],
    context: RunContext,
    registry: ComponentRegistry,
    event_bus: EventBus,
) -> list[dict]:
    """多编辑并行产出草稿（A/B 测试）"""
    import asyncio

    from content_factory_writing import WritingProvider

    writing = WritingProvider(registry=registry, event_bus=event_bus)

    tasks = []
    for slug in editor_slugs:
        tasks.append(writing.write_article(topic, slug, context))

    drafts = await asyncio.gather(*tasks, return_exceptions=True)

    results = []
    for slug, draft in zip(editor_slugs, drafts, strict=False):
        if isinstance(draft, Exception):
            logger.error("parallel_draft_failed", editor=slug, error=str(draft))
            results.append(
                {
                    "editor": slug,
                    "status": "failed",
                    "error": str(draft),
                }
            )
        else:
            results.append(
                {
                    "editor": slug,
                    "status": "success",
                    "draft_id": str(draft.id),
                    "content": draft.content,
                    "length": len(draft.content),
                }
            )

    return results


class FeedbackTracker:
    """
    数据回流跟踪器（简化实现）

    记录每篇文章的发布后表现，用于反馈优化风格指纹。
    """

    def __init__(self):
        self._feedback: dict[str, dict] = {}

    def record_feedback(self, article_id: UUID, metrics: dict) -> None:
        """记录文章表现指标"""
        self._feedback[str(article_id)] = {
            "metrics": metrics,
            "recorded_at": __import__("datetime").datetime.now().isoformat(),
        }
        logger.info("feedback_recorded", article_id=str(article_id), metrics=metrics)

    def get_feedback(self, article_id: UUID) -> dict | None:
        """获取文章反馈"""
        return self._feedback.get(str(article_id))

    def aggregate_by_editor(self, editor_slug: str) -> dict:
        """按编辑器聚合反馈"""
        # 简化实现：实际应查询数据库
        return {
            "editor": editor_slug,
            "article_count": len(self._feedback),
            "note": "需要接入真实数据源",
        }


# 全局反馈跟踪器
_feedback_tracker = FeedbackTracker()


def get_feedback_tracker() -> FeedbackTracker:
    return _feedback_tracker
