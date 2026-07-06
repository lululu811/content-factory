"""
严肃派编辑组件

风格特点：
- 语气严肃、专业
- 注重数据和逻辑
- 避免口语化表达
- 常用词汇：「值得注意的是」「从数据来看」「综上所述」
"""

from datetime import datetime
from typing import Any
from uuid import uuid4

from content_factory_core.models import Draft, Editor, RunContext, Topic
from content_factory_sdk.spi import EditorProvider


class YanSuEditor(EditorProvider):
    """严肃派编辑"""

    def __init__(self) -> None:
        self.editor = Editor(
            id=uuid4(),
            tenant_id=uuid4(),  # 实际使用时从配置加载
            name="严肃派",
            slug="yan-su-pai",
            style_fingerprint={
                "tone": "严肃",
                "formality": 0.9,
                "vocabulary": [
                    "值得注意的是",
                    "从数据来看",
                    "综上所述",
                    "不可忽视",
                    "深入分析",
                    "显而易见",
                ],
                "sentence_length": "中等偏长",
                "paragraph_structure": "总-分-总",
            },
            preferences={
                "preferred_industries": ["科技", "新能源", "医药"],
                "risk_tolerance": 0.3,  # 保守
                "target_audience": "专业投资者",
            },
        )

    async def draft_article(
        self, topic: Topic, context: RunContext
    ) -> Draft:
        """
        根据选题生成草稿

        实际实现会调用 LLM，这里返回 mock 内容。
        """
        content = f"""# {topic.title}

## 核心观点

值得注意的的是，{topic.description or '这一主题值得深入分析'}。

## 数据支撑

从数据来看，相关指标呈现出明显的趋势。深入分析后发现，背后的驱动因素主要包括以下几点：

1. **因素一**：不可忽视的结构性变化
2. **因素二**：显而易见的政策支持
3. **因素三**：市场预期的修正

## 风险提示

综上所述，投资者应当理性看待，注意控制风险。

---
*免责声明：本文仅代表作者观点，不构成投资建议。*
"""
        return Draft(
            tenant_id=context.tenant_id,
            topic_id=topic.id,
            editor_id=self.editor.id,
            content=content,
            metadata={
                "editor": "yan-su-pai",
                "style": "严肃派",
                "word_count": len(content),
                "generated_at": datetime.utcnow().isoformat(),
            },
        )

    def style_fingerprint(self) -> dict[str, Any]:
        """返回风格指纹"""
        return self.editor.style_fingerprint or {}

    def can_handle(self, topic: Topic) -> bool:
        """
        判断是否能处理这个选题
        基于编辑的偏好（行业、风险容忍度等）
        """
        # 简单实现：检查选题标签是否在偏好行业中
        preferred = self.editor.preferences.get("preferred_industries", [])
        if not preferred:
            return True  # 没有偏好限制
        return any(tag in preferred for tag in topic.tags)
