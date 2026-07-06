"""
多租户管理器

提供租户隔离的数据存储。
支持两种后端:
  - InMemory（默认）: 开发/测试用，无外部依赖
  - PostgreSQL: 生产环境，schema-level 隔离（需要 psycopg）
"""

from typing import Any
from uuid import UUID

import structlog

from content_factory_core.models import Tenant

logger = structlog.get_logger()


class TenantManager:
    """内存租户管理器（默认）"""

    def __init__(self) -> None:
        self._tenants: dict[UUID, Tenant] = {}
        self._tenant_data: dict[UUID, dict[str, Any]] = {}
        logger.info("tenant_manager_initialized", backend="memory")

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


class PostgreSQLTenantManager(TenantManager):
    """
    PostgreSQL 租户管理器（schema-level 隔离）

    每个租户对应一个独立 schema，实现真正的数据隔离。

    需要环境变量: CF_DATABASE_URL (postgresql://user:pass@host/db)
    需要依赖: psycopg[binary]

    Schema 结构:
      tenant_{slug}/runs
      tenant_{slug}/articles
      tenant_{slug}/editors
    """

    def __init__(self, database_url: str | None = None) -> None:
        try:
            import psycopg
            from psycopg.rows import dict_row
        except ImportError:
            raise RuntimeError(
                "PostgreSQL 后端需要安装 psycopg。"
                "运行: pip install 'psycopg[binary]'"
            )

        self._database_url = database_url or __import__("os").getenv("CF_DATABASE_URL")
        if not self._database_url:
            raise RuntimeError(
                "需要设置 CF_DATABASE_URL 环境变量 "
                "(例如: postgresql://user:pass@localhost:5432/content_factory)"
            )

        self._psycopg = psycopg
        self._dict_row = dict_row
        self._initialized = False
        logger.info("tenant_manager_initialized", backend="postgresql")

        # 基类初始化（内存缓存用于快速查询）
        super().__init__()

    def _get_connection(self):
        """获取数据库连接"""
        return self._psycopg.connect(self._database_url, row_factory=self._dict_row)

    def _ensure_schema(self, slug: str) -> None:
        """确保租户 schema 存在"""
        schema_name = f"tenant_{slug.replace('-', '_')}"
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")
                cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS {schema_name}.runs (
                        run_id UUID PRIMARY KEY,
                        topic_title TEXT NOT NULL,
                        editor_slug TEXT NOT NULL,
                        status TEXT NOT NULL,
                        duration_seconds FLOAT,
                        created_at TIMESTAMPTZ DEFAULT NOW()
                    )
                """)
                cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS {schema_name}.articles (
                        article_id UUID PRIMARY KEY,
                        run_id UUID REFERENCES {schema_name}.runs(run_id),
                        title TEXT NOT NULL,
                        url TEXT,
                        created_at TIMESTAMPTZ DEFAULT NOW()
                    )
                """)
        logger.info("schema_ensured", schema=schema_name)

    def create_tenant(self, name: str, slug: str) -> Tenant:
        """创建租户 + 初始化 schema"""
        tenant = super().create_tenant(name, slug)
        try:
            self._ensure_schema(slug)
            logger.info("tenant_postgres_initialized", tenant_id=str(tenant.id))
        except Exception as e:
            logger.error(
                "tenant_schema_failed",
                tenant_id=str(tenant.id),
                error=str(e),
            )
            # 降级：继续用内存
        return tenant

    def add_run(self, tenant_id: UUID, run_data: dict[str, Any]) -> None:
        """添加运行记录（双写：内存 + PostgreSQL）"""
        super().add_run(tenant_id, run_data)
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            return
        try:
            schema = f"tenant_{tenant.slug.replace('-', '_')}"
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f"""
                        INSERT INTO {schema}.runs
                        (run_id, topic_title, editor_slug, status, duration_seconds)
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (
                            run_data["run_id"],
                            run_data["topic_title"],
                            run_data["editor_slug"],
                            run_data["status"],
                            run_data.get("duration_seconds"),
                        ),
                    )
        except Exception as e:
            logger.warning("postgres_write_fallback", error=str(e))

    def add_article(self, tenant_id: UUID, article_data: dict[str, Any]) -> None:
        """添加文章（双写）"""
        super().add_article(tenant_id, article_data)
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            return
        try:
            schema = f"tenant_{tenant.slug.replace('-', '_')}"
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f"""
                        INSERT INTO {schema}.articles
                        (article_id, run_id, title, url)
                        VALUES (%s, %s, %s, %s)
                        """,
                        (
                            article_data["article_id"],
                            article_data.get("run_id"),
                            article_data["title"],
                            article_data.get("url"),
                        ),
                    )
        except Exception as e:
            logger.warning("postgres_write_fallback", error=str(e))


# ============== Factory ==============


def create_tenant_manager(backend: str = "auto") -> TenantManager:
    """
    创建租户管理器

    backend:
      - "auto": 自动选择（CF_DATABASE_URL 存在则 PostgreSQL，否则内存）
      - "memory": 强制内存
      - "postgresql": 强制 PostgreSQL（需要 CF_DATABASE_URL）
    """
    import os

    if backend == "auto":
        backend = "postgresql" if os.getenv("CF_DATABASE_URL") else "memory"

    if backend == "memory":
        return TenantManager()
    elif backend == "postgresql":
        return PostgreSQLTenantManager()
    else:
        raise ValueError(f"Unknown backend: {backend}")


# 全局单例
_tenant_manager: TenantManager | None = None


def get_tenant_manager() -> TenantManager:
    """获取全局租户管理器"""
    global _tenant_manager
    if _tenant_manager is None:
        _tenant_manager = create_tenant_manager()
    return _tenant_manager
