"""
犀利派编辑组件

风格特点：
- 语气直接、犀利
- 口语化表达
- 敢于表达强烈观点
- 常用词汇：「说人话就是」「别装了」「真相是」「醒醒吧」
"""

from datetime import datetime
from typing import Any
from uuid import uuid4

from content_factory_core.models import Draft, Editor, RunContext, Topic
from content_factory_sdk.spi import EditorProvider


class XiLiEditor(EditorProvider):
    """犀利派编辑"""

    def __init__(self) -> None:
        self.editor = Editor(
            id=uuid4(),
            tenant_id=uuid4(),
            name="犀利派",
            slug="xi-li-pai",
            style_fingerprint={
                "tone": "犀利",
                "formality": 0.3,
                "vocabulary": [
                    "说人话就是",
                    "别装了",
                    "真相是",
                    "醒醒吧",
                    "说白了",
                    "扯淡",
                    "忽悠",
                    "割韭菜",
                    "血淋淋",
                    "打脸",
                ],
                "sentence_length": "短",
                "paragraph_structure": "开门见山",
                "emotional_intensity": 0.8,
            },
            preferences={
                "preferred_industries": ["消费", "互联网", "房地产"],
                "risk_tolerance": 0.8,  # 激进
                "target_audience": "散户投资者",
                "style": "敢说真话、不装逼、接地气",
            },
        )

    async def draft_article(self, topic: Topic, context: RunContext) -> Draft:
        """
        根据选题生成草稿
        犀利派风格：开门见山、直抒胸臆、不绕弯子
        """
        content = f"""# {topic.title}：别被忽悠了，真相在这

## 开门见山

说人话就是，{topic.description or "这事没那么简单"}。别装了，大家都心知肚明，只是没人敢说而已。

## 真相是

醒醒吧！市场里的水有多深，你知道吗？

**血淋淋的现实**：
1. 所谓的"利好"，不过是机构出货的幌子
2. 散户看到的"机会"，往往是别人精心设计的陷阱
3. 你以为的"价值投资"，可能 just 是被割韭菜的借口

## 说白了

这事的核心逻辑就三点：

- **第一**：别信那些券商研报，99% 都是忽悠
- **第二**：跟着感觉走？那你等着亏钱吧
- **第三**：真正的高手，都在别人恐惧时贪婪

## 我的观点

我的观点很简单：**别怂，但也别傻**。

看不懂的东西就别碰，看得懂的东西就狠狠干。别整天听这个分析师那个大V的，他们要是真能预测市场，早就财务自由了，还用得着在这忽悠你？

## 风险提示

最后说句实话：本文纯属个人观点，不构成任何投资建议。你要是照着做了还亏钱，别来找我，因为我自己也可能亏钱。

---
*犀利派 · 说真话不装逼*
"""
        return Draft(
            tenant_id=context.tenant_id,
            topic_id=topic.id,
            editor_id=self.editor.id,
            content=content,
            metadata={
                "editor": "xi-li-pai",
                "style": "犀利派",
                "word_count": len(content),
                "generated_at": datetime.utcnow().isoformat(),
                "tone": "direct",
                "emotional_intensity": 0.8,
            },
        )

    def style_fingerprint(self) -> dict[str, Any]:
        """返回风格指纹"""
        return self.editor.style_fingerprint or {}

    def can_handle(self, topic: Topic) -> bool:
        """
        判断是否能处理这个选题
        犀利派偏好：消费、互联网、房地产、散户关心的话题
        """
        preferred = self.editor.preferences.get("preferred_industries", [])
        if not preferred:
            return True
        return any(tag in preferred for tag in topic.tags)
