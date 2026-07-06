"""
合规模型定义

定义合规检查的结果模型。
"""

from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class CheckStatus(str, Enum):
    """检查状态"""
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"
    ERROR = "ERROR"


class ComplianceCheck(BaseModel):
    """单个合规检查项"""
    code: str  # 如 "A1", "B8"
    name: str  # 如 "标题长度", "免责声明"
    status: CheckStatus
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class ComplianceResult(BaseModel):
    """合规检查整体结果"""
    draft_id: UUID
    article_slug: str
    checks: list[ComplianceCheck]

    @property
    def passed_count(self) -> int:
        return sum(1 for c in self.checks if c.status == CheckStatus.PASS)

    @property
    def warned_count(self) -> int:
        return sum(1 for c in self.checks if c.status == CheckStatus.WARN)

    @property
    def failed_count(self) -> int:
        return sum(1 for c in self.checks if c.status == CheckStatus.FAIL)

    @property
    def error_count(self) -> int:
        return sum(1 for c in self.checks if c.status == CheckStatus.ERROR)

    @property
    def has_failures(self) -> bool:
        return self.failed_count > 0 or self.error_count > 0

    @property
    def can_publish(self) -> bool:
        """是否可以发布（无 FAIL 和 ERROR）"""
        return not self.has_failures

    def summary(self) -> str:
        """返回人类可读的摘要"""
        if self.has_failures:
            return f"❌ 不可发布：{self.failed_count} FAIL + {self.error_count} ERROR"
        elif self.warned_count > 0:
            return f"⚠️ 可发布但有风险：{self.warned_count} WARN"
        else:
            return f"✅ 可发布：{self.passed_count}/{len(self.checks)} PASS"
