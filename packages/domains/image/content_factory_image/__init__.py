"""
配图领域组件

提供图表生成、图片处理等功能。
"""

from typing import Any
from uuid import UUID


class ImageProvider:
    """配图提供者"""

    async def generate_images(self, draft_id: UUID, content: str) -> list[str]:
        """
        根据内容生成配图
        返回图片路径列表
        """
        # Mock 实现
        return [
            f"images/{draft_id}_chart1.png",
            f"images/{draft_id}_chart2.png",
        ]

    async def validate_images(self, image_paths: list[str]) -> dict[str, Any]:
        """验证图片是否符合要求"""
        return {
            "valid": len(image_paths) >= 5,
            "count": len(image_paths),
            "issues": [] if len(image_paths) >= 5 else ["图片数量不足"],
        }
