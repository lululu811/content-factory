"""
多租户管理器

提供租户隔离的数据存储。
"""

from typing import Any
from uuid import UUID

import structlog

from content_factory_core.models import Tenant

logger = structlog.get_logger()


class TenantManager:
    """多租户管理器"""

    def __init__(self) -> None:
        # 内存存储（生产环境应替换为数据库）
        self._tenants: dict[UUID, Tenant] = {}
        self._tenant_data: dict[UUID, dict[str, Any]] = {}
        logger.info("tenant_manager_initialized")

    def create_tenant(self, name: str, slug: str) -> Tenant:
        """创建租户"""
        import uuid
        tenant = Tenant(id=uuid.uuid4(), name=name, slug=slug)
        self._tenants[tenant.id] = tenant
        self._tenant_data[tenant.id] = {
            "runs": [],
            "articles": [],
            "editors": [],
        }
        logger.info("tenant_created", tenant_id=str(tenant.id), name=name)
        return tenant

    def get_tenant(self, tenant_id: UUID) -> Tenant | None:
        """获取租户"""
        return self._tenants.get(tenant_id)

    def list_tenants(self) -> list[Tenant]:
        """列出所有租户"""
        return list(self._tenants.values())

    def get_tenant_data(self, tenant_id: UUID) -> dict[str, Any]:
        """获取租户数据"""
        if tenant_id not in self._tenant_data:
            raise ValueError(f"Tenant not found: {tenant_id}")
        return self._tenant_data[tenant_id]

    def add_run(self, tenant_id: UUID, run_data: dict[str, Any]) -> None:
        """添加运行记录"""
        if tenant_id not in self._tenant_data:
            raise ValueError(f"Tenant not found: {tenant_id}")
        self._tenant_data[tenant_id]["runs"].append(run_data)

    def get_runs(self, tenant_id: UUID) -> list[dict[str, Any]]:
        """获取运行记录"""
        if tenant_id not in self._tenant_data:
            raise ValueError(f"Tenant not found: {tenant_id}")
        return self._tenant_data[tenant_id]["runs"]

    def add_article(self, tenant_id: UUID, article_data: dict[str, Any]) -> None:
        """添加文章"""
        if tenant_id not in self._tenant_data:
            raise ValueError(f"Tenant not found: {tenant_id}")
        self._tenant_data[tenant_id]["articles"].append(article_data)

    def get_articles(self, tenant_id: UUID) -> list[dict[str, Any]]:
        """获取文章"""
        if tenant_id not in self._tenant_data:
            raise ValueError(f"Tenant not found: {tenant_id}")
        return self._tenant_data[tenant_id]["articles"]


# 全局单例
_tenant_manager: TenantManager | None = None


def get_tenant_manager() -> TenantManager:
    """获取全局租户管理器"""
    global _tenant_manager
    if _tenant_manager is None:
        _tenant_manager = TenantManager()
    return _tenant_manager
