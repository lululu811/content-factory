"""
FastAPI 应用

创建和配置 HTTP API 服务。
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from uuid import UUID, uuid4

from content_factory_core.models import RunContext, Tenant, Topic
from content_factory_sdk import InMemoryEventBus, discover_components
from content_factory_topic import TopicProvider
from content_factory_research import DefaultResearchProvider
from content_factory_writing import WritingProvider
from content_factory_compliance import DefaultComplianceProvider
from content_factory_image import ImageProvider
from content_factory_publish import PublishProvider
from content_factory_tushare import TushareDataSource


class CreateRunRequest(BaseModel):
    """创建运行请求"""
    tenant_name: str
    topic_title: Optional[str] = None
    editor_slug: Optional[str] = None


class RunResponse(BaseModel):
    """运行响应"""
    run_id: UUID
    status: str
    topic_title: str
    editor_slug: str
    draft_length: int
    compliance_passed: bool
    publish_url: Optional[str] = None


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    version: str
    components: dict


# 全局状态（生产环境应该用数据库）
runs: dict[UUID, RunResponse] = {}


def create_app() -> FastAPI:
    """创建 FastAPI 应用"""
    app = FastAPI(
        title="Content Factory API",
        description="投研内容 AI 编辑部操作系统",
        version="0.3.0",
    )

    @app.get("/health", response_model=HealthResponse)
    async def health_check():
        """健康检查"""
        registry = discover_components()
        return HealthResponse(
            status="healthy",
            version="0.3.0",
            components=registry.list_components(),
        )

    @app.post("/runs", response_model=RunResponse)
    async def create_run(request: CreateRunRequest):
        """
        创建新的文章生产运行

        执行完整工作流：选题 → 研究 → 写作 → 合规 → 发布
        """
        # 初始化基础设施
        event_bus = InMemoryEventBus()
        registry = discover_components()

        # 创建租户和上下文
        tenant_slug = f"tenant-{uuid4().hex[:8]}"
        tenant = Tenant(name=request.tenant_name, slug=tenant_slug)
        context = RunContext(tenant_id=tenant.id, topic_id=uuid4())

        # 1. 选题
        topic_provider = TopicProvider(event_bus=event_bus)
        if request.topic_title:
            topic = Topic(
                tenant_id=tenant.id,
                title=request.topic_title,
                tags=["科技"],
            )
        else:
            topics = await topic_provider.discover_topics(context)
            if not topics:
                raise HTTPException(status_code=400, detail="No topics available")
            topic = topics[0]

        context.topic_id = topic.id
        await topic_provider.approve_topic(topic, context)

        # 2. 研究
        tushare = TushareDataSource()
        research_provider = DefaultResearchProvider(
            data_sources=[tushare],
            event_bus=event_bus,
        )
        await research_provider.run_research(topic, context)

        # 3. 写作
        writing_provider = WritingProvider(registry=registry, event_bus=event_bus)
        editor_slug = request.editor_slug or await writing_provider.select_editor(topic)
        draft = await writing_provider.write_article(topic, editor_slug, context)

        # 4. 合规检查
        compliance_provider = DefaultComplianceProvider()
        compliance_result = await compliance_provider.check(draft)

        # 5. 配图和发布
        image_provider = ImageProvider()
        images = await image_provider.generate_images(draft.id, draft.content)

        # 批准草稿（即使合规未通过也强制批准，用于测试）
        article = await compliance_provider.approve(draft)
        article.images = images

        publish_provider = PublishProvider(event_bus=event_bus)
        publish_event = await publish_provider.publish(article)

        # 构建响应
        run_id = uuid4()
        run_response = RunResponse(
            run_id=run_id,
            status="completed",
            topic_title=topic.title,
            editor_slug=editor_slug,
            draft_length=len(draft.content),
            compliance_passed=compliance_result["passed"],
            publish_url=publish_event.publish_url,
        )

        runs[run_id] = run_response
        return run_response

    @app.get("/runs/{run_id}", response_model=RunResponse)
    async def get_run(run_id: UUID):
        """获取运行状态"""
        if run_id not in runs:
            raise HTTPException(status_code=404, detail="Run not found")
        return runs[run_id]

    @app.get("/runs")
    async def list_runs():
        """列出所有运行"""
        return {
            "total": len(runs),
            "runs": [run.dict() for run in runs.values()],
        }

    return app


# 创建默认应用实例
app = create_app()
