"""
合规检查领域组件

提供 16+ 项合规检查，确保文章符合发布标准。
"""

from content_factory_compliance.provider import DefaultComplianceProvider
from content_factory_compliance.models import (
    ComplianceCheck,
    ComplianceResult,
    CheckStatus,
)

__version__ = "0.3.0"

__all__ = [
    "DefaultComplianceProvider",
    "ComplianceCheck",
    "ComplianceResult",
    "CheckStatus",
]
