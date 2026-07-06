"""
FastAPI 应用

集成:
- HTTP API（文章生产、租户管理、监控）
- Web UI（管理界面）
- 多编辑风格 A/B 测试
- 可观测性（OpenTelemetry 降级模式）
- 多租户隔离
"""
import asyncio
import time
from typing import Optional
from uuid import UUID, uuid4, uuid5

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from content_factory_core.models import RunContext, Tenant, Topic
from content_factory_core.tenant_manager import get_tenant_manager
from content_factory_sdk import InMemoryEventBus, discover_components
from content_factory_sdk.ab_testing import (
    get_feedback_tracker,
    parallel_draft,
)
from content_factory_topic import TopicProvider
from content_factory_research import DefaultResearchProvider
from content_factory_writing import WritingProvider
from content_factory_compliance import DefaultComplianceProvider
from content_factory_image import ImageProvider
from content_factory_publish import PublishProvider
from content_factory_tushare import TushareDataSource

from content_factory_server.observability import (
    get_metrics_snapshot,
    init_tracing,
    record_workflow_run,
    trace_span,
)

# 用于从 editor slug 生成确定性 UUID
EDITOR_NAMESPACE = UUID("00000000-0000-4000-8000-000000000000")


def slug_to_editor_id(slug: str) -> UUID:
    """将 editor slug 转为确定性 UUID"""
    return uuid5(EDITOR_NAMESPACE, slug)


class CreateRunRequest(BaseModel):
    """创建运行请求"""
    tenant_name: str
    topic_title: Optional[str] = None
    editor_slug: Optional[str] = None
    ab_test: bool = False  # A/B 测试模式


class TenantCreateRequest(BaseModel):
    """创建租户请求"""
    name: str


class HealthResponse(BaseModel):
    """健康检查"""
    status: str
    version: str
    components: dict


def create_app() -> FastAPI:
    """创建 FastAPI 应用"""
    app = FastAPI(
        title="Content Factory API",
        description="投研内容 AI 编辑部操作系统",
        version="0.3.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 初始化追踪
    init_tracing("content-factory")

    # 租户管理器
    tenant_manager = get_tenant_manager()

    @app.get("/health", response_model=HealthResponse)
    async def health_check():
        """健康检查"""
        registry = discover_components()
        return HealthResponse(
            status="healthy",
            version="0.3.0",
            components=registry.list_components(),
        )

    # ============== 多租户管理 ==============

    @app.post("/tenants")
    async def create_tenant(request: TenantCreateRequest):
        """创建租户"""
        slug = f"tenant-{uuid4().hex[:8]}"
        tenant = tenant_manager.create_tenant(request.name, slug)
        return {
            "tenant_id": str(tenant.id),
            "name": tenant.name,
            "slug": tenant.slug,
        }

    @app.get("/tenants")
    async def list_tenants():
        """列出所有租户"""
        tenants = tenant_manager.list_tenants()
        return {
            "total": len(tenants),
            "tenants": [
                {
                    "tenant_id": str(t.id),
                    "name": t.name,
                    "slug": t.slug,
                }
                for t in tenants
            ],
        }

    # ============== 文章生产 ==============

    @app.post("/runs")
    async def create_run(request: CreateRunRequest):
        """
        创建新的文章生产运行

        支持 A/B 测试模式（多编辑并行产出）。
        """
        start_time = time.time()

        with trace_span("workflow.run", {"tenant": request.tenant_name}):
            # 初始化基础设施
            event_bus = InMemoryEventBus()
            registry = discover_components()

            # 创建或获取租户
            existing = [t for t in tenant_manager.list_tenants() if t.name == request.tenant_name]
            if existing:
                tenant = existing[0]
            else:
                tenant_slug = f"tenant-{uuid4().hex[:8]}"
                tenant = tenant_manager.create_tenant(request.tenant_name, tenant_slug)

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

            # 3. 写作（支持 A/B 测试）
            if request.ab_test:
                # 多编辑并行产出（传入 slug 字符串列表）
                all_editor_slugs = registry.list_components().get("editors", [])
                if not all_editor_slugs:
                    raise HTTPException(status_code=400, detail="No editors available")

                drafts_results = await parallel_draft(
                    topic, all_editor_slugs, context, registry, event_bus
                )
                # 返回第一个成功的草稿作为主结果
                successful = [d for d in drafts_results if d["status"] == "success"]
                if not successful:
                    raise HTTPException(status_code=500, detail="All editors failed")

                draft = successful[0]
                editor_slug = draft["editor"]
                draft_content = draft["content"]
                ab_results = drafts_results
            else:
                # 单编辑模式
                writing_provider = WritingProvider(registry=registry, event_bus=event_bus)
                editor_slug = request.editor_slug or await writing_provider.select_editor(topic)
                draft = await writing_provider.write_article(topic, editor_slug, context)
                draft_content = draft.content
                ab_results = None

            # 4. 合规检查
            compliance_provider = DefaultComplianceProvider()
            # 创建临时 Draft 对象用于合规检查
            from content_factory_core.models import Draft
            temp_draft = Draft(
                id=uuid4(),
                tenant_id=tenant.id,
                topic_id=topic.id,
                editor_id=slug_to_editor_id(editor_slug),
                content=draft_content,
            )
            compliance_result = await compliance_provider.check(temp_draft)

            # 5. 配图和发布
            image_provider = ImageProvider()
            images = await image_provider.generate_images(temp_draft.id, draft_content)

            article = await compliance_provider.approve(temp_draft)
            article.images = images

            publish_provider = PublishProvider(event_bus=event_bus)
            publish_event = await publish_provider.publish(article)

            # 记录指标
            duration = time.time() - start_time
            record_workflow_run(
                tenant_id=str(tenant.id),
                editor_slug=editor_slug,
                duration_seconds=duration,
                compliance_passed=compliance_result["passed"],
                status="completed",
            )

            # 存储运行记录
            run_id = uuid4()
            tenant_manager.add_run(tenant.id, {
                "run_id": str(run_id),
                "topic_title": topic.title,
                "editor_slug": editor_slug,
                "status": "completed",
                "duration_seconds": duration,
            })
            tenant_manager.add_article(tenant.id, {
                "article_id": str(article.id),
                "run_id": str(run_id),
                "title": topic.title,
                "url": publish_event.publish_url,
            })

            response = {
                "run_id": str(run_id),
                "tenant_id": str(tenant.id),
                "status": "completed",
                "topic_title": topic.title,
                "editor_slug": editor_slug,
                "draft_length": len(draft_content),
                "compliance_passed": compliance_result["passed"],
                "publish_url": publish_event.publish_url,
            }
            if ab_results:
                response["ab_test_results"] = ab_results

            return response

    @app.get("/runs")
    async def list_runs(tenant_id: Optional[str] = None):
        """列出运行记录"""
        if tenant_id:
            try:
                tid = UUID(tenant_id)
                runs = tenant_manager.get_runs(tid)
            except Exception:
                raise HTTPException(status_code=404, detail="Tenant not found")
        else:
            runs = []
            for tenant in tenant_manager.list_tenants():
                runs.extend(tenant_manager.get_runs(tenant.id))

        return {"total": len(runs), "runs": runs}

    @app.get("/runs/{run_id}")
    async def get_run(run_id: UUID):
        """获取运行详情"""
        # 在所有租户中查找
        for tenant in tenant_manager.list_tenants():
            for run in tenant_manager.get_runs(tenant.id):
                if run.get("run_id") == str(run_id):
                    return run
        raise HTTPException(status_code=404, detail="Run not found")

    # ============== Web UI ==============

    @app.get("/", response_class=HTMLResponse)
    async def admin_dashboard():
        """管理后台首页"""
        tenants = tenant_manager.list_tenants()
        registry = discover_components()
        components = registry.list_components()

        html = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Content Factory - 管理后台</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
                .container {{ max-width: 1200px; margin: 0 auto; }}
                h1 {{ color: #1a1a1a; border-bottom: 2px solid #007bff; padding-bottom: 10px; }}
                .card {{ background: white; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; }}
                .stat {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; }}
                .stat-value {{ font-size: 2em; font-weight: bold; }}
                .stat-label {{ font-size: 0.9em; opacity: 0.9; }}
                .component-list {{ display: flex; flex-wrap: wrap; gap: 10px; }}
                .component-tag {{ background: #e9ecef; padding: 5px 12px; border-radius: 20px; font-size: 0.85em; }}
                table {{ width: 100%; border-collapse: collapse; }}
                th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #dee2e6; }}
                th {{ background: #f8f9fa; font-weight: 600; }}
                .api-section {{ margin-top: 30px; }}
                .api-endpoint {{ background: #f8f9fa; padding: 10px; border-radius: 4px; font-family: monospace; margin: 5px 0; }}
                .method {{ display: inline-block; width: 60px; font-weight: bold; }}
                .method-get {{ color: #28a745; }}
                .method-post {{ color: #007bff; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🏭 Content Factory 管理后台</h1>

                <div class="stats">
                    <div class="stat">
                        <div class="stat-value">{len(tenants)}</div>
                        <div class="stat-label">租户</div>
                    </div>
                    <div class="stat">
                        <div class="stat-value">{sum(len(components.get(k, [])) for k in components)}</div>
                        <div class="stat-label">组件</div>
                    </div>
                    <div class="stat">
                        <div class="stat-value">{sum(len(tenant_manager.get_runs(t.id)) for t in tenants)}</div>
                        <div class="stat-label">运行记录</div>
                    </div>
                    <div class="stat">
                        <div class="stat-value">v0.3.0</div>
                        <div class="stat-label">版本</div>
                    </div>
                </div>

                <div class="card">
                    <h2>📦 已注册组件</h2>
                    <div class="component-list">
                        {''.join(f'<span class="component-tag">{k}: {len(v)}</span>' for k, v in components.items())}
                    </div>
                </div>

                <div class="card">
                    <h2>🏢 租户列表</h2>
                    <table>
                        <thead>
                            <tr>
                                <th>名称</th>
                                <th>Slug</th>
                                <th>运行数</th>
                            </tr>
                        </thead>
                        <tbody>
                            {''.join(f'<tr><td>{t.name}</td><td>{t.slug}</td><td>{len(tenant_manager.get_runs(t.id))}</td></tr>' for t in tenants) or '<tr><td colspan="3" style="text-align:center;color:#999;">暂无租户</td></tr>'}
                        </tbody>
                    </table>
                </div>

                <div class="card api-section">
                    <h2>🔌 API 端点</h2>
                    <div class="api-endpoint"><span class="method method-get">GET</span> /health - 健康检查</div>
                    <div class="api-endpoint"><span class="method method-post">POST</span> /tenants - 创建租户</div>
                    <div class="api-endpoint"><span class="method method-get">GET</span> /tenants - 租户列表</div>
                    <div class="api-endpoint"><span class="method method-post">POST</span> /runs - 创建运行（支持 A/B 测试）</div>
                    <div class="api-endpoint"><span class="method method-get">GET</span> /runs - 运行记录</div>
                    <div class="api-endpoint"><span class="method method-get">GET</span> /metrics - 指标快照</div>
                </div>
            </div>
        </body>
        </html>
        """
        return html

    # ============== 可观测性 ==============

    @app.get("/metrics")
    async def metrics_endpoint():
        """指标快照"""
        return get_metrics_snapshot()

    return app


app = create_app()
