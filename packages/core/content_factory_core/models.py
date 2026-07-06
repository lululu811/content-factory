"""
核心领域模型

定义系统的一等公民：Tenant, Topic, Editor, Draft, Article
"""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Tenant(BaseModel):
    """租户（多租户平台的一等公民）"""
    id: UUID = Field(default_factory=uuid4)
    name: str
    slug: str = Field(..., pattern=r"^[a-z0-9-]+$")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True


class Topic(BaseModel):
    """选题"""
    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    title: str
    description: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    score: Optional[float] = None
    status: str = "pending"  # pending / approved / rejected / completed
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Editor(BaseModel):
    """编辑（AI persona 或真人数字化）"""
    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    name: str
    slug: str = Field(..., pattern=r"^[a-z0-9-]+$")
    style_fingerprint: Optional[dict] = None  # 风格指纹（从样本学习）
    preferences: dict = Field(default_factory=dict)  # 选题偏好、合规尺度等
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Draft(BaseModel):
    """草稿"""
    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    topic_id: UUID
    editor_id: UUID
    content: str
    metadata: dict = Field(default_factory=dict)
    version: int = 1
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Article(BaseModel):
    """终稿（通过合规审查的草稿）"""
    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    topic_id: UUID
    editor_id: UUID
    draft_id: UUID
    title: str
    content: str
    images: list[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)
    status: str = "ready"  # ready / published / archived
    created_at: datetime = Field(default_factory=datetime.utcnow)


class RunContext(BaseModel):
    """运行上下文（workflow 执行时的上下文信息）"""
    run_id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    topic_id: UUID
    editor_id: Optional[UUID] = None
    started_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict = Field(default_factory=dict)
