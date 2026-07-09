"""
配置管理

使用 pydantic-settings 管理配置，支持环境变量覆盖。
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """全局配置"""

    model_config = SettingsConfigDict(
        env_prefix="CF_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # 应用
    app_name: str = "content-factory"
    app_env: str = "development"  # development / staging / production
    debug: bool = False

    # 数据库
    database_url: str = "postgresql://localhost:5432/content_factory"
    database_schema_prefix: str = "tenant"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Temporal
    temporal_host: str = "localhost:7233"
    temporal_namespace: str = "content-factory"

    # 多租户
    default_tenant_id: str | None = None

    # 日志
    log_level: str = "INFO"
    log_format: str = "json"  # json / console


class TenantSettings(BaseSettings):
    """租户级配置（可从数据库加载）"""

    tenant_id: str
    max_concurrent_runs: int = 5
    allowed_editors: list[str] = Field(default_factory=list)
    allowed_data_sources: list[str] = Field(default_factory=list)
    custom_config: dict = Field(default_factory=dict)
