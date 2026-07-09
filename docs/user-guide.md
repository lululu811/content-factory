# content-factory 使用手册

> 本文档是 content-factory 平台的完整使用指南，覆盖从开发模式到生产部署的全场景。

## 目录

1. [快速开始](#快速开始)
2. [架构概览](#架构概览)
3. [HTTP API 参考](#http-api-参考)
4. [CLI 命令参考](#cli-命令参考)
5. [核心概念详解](#核心概念详解)
6. [多租户管理](#多租户管理)
7. [文章生产工作流](#文章生产工作流)
8. [多编辑风格与 A/B 测试](#多编辑风格与-ab-测试)
9. [合规检查](#合规检查)
10. [微信公众号发布](#微信公众号发布)
11. [外部数据源与知识库](#外部数据源与知识库)
12. [可观测性](#可观测性)
13. [Temporal 编排](#temporal-编排)
14. [Web UI 管理后台](#web-ui-管理后台)
15. [开发新组件](#开发新组件)
16. [生产部署](#生产部署)
17. [故障排查](#故障排查)

---

## 快速开始

### 1. 环境要求

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (推荐) 或 pip
- Docker (可选，用于 Temporal)

### 2. 安装

```bash
git clone https://github.com/lululu811/content-factory.git
cd content-factory
uv sync --all-packages
```

### 3. 启动服务

```bash
# HTTP 服务（开发模式）
uv run uvicorn content_factory_server.app:app --reload --port 8000
```

访问 http://localhost:8000/ 即可看到管理后台。

### 4. 第一篇文档

```bash
# 通过 CLI
uv run cf create --tenant "我的团队" --topic "AI Agent 深度报告"

# 通过 curl
curl -X POST http://localhost:8000/runs \
  -H "Content-Type: application/json" \
  -d '{"tenant_name": "我的团队", "topic_title": "AI Agent 深度报告"}'
```

---

## 架构概览

### 四层架构

```
┌─ Applications ─── CLI · HTTP API · Web UI ─────────────────┐
├─ Orchestration ── Temporal · Event Bus · A/B Testing ──────┤
├─ Components ───── topic · research · writing · compliance ─┤
│                    image · publish · editors · adapters     │
├─ Platform ─────── Core · SDK SPI · Registry · OTel ────────┤
│                    TenantManager                            │
└────────────────────────────────────────────────────────────┘
```

### 数据流

```
HTTP 请求
  ↓
FastAPI → create_run()
  ├─→ TopicProvider.discover_topics()
  ├─→ TopicProvider.approve_topic()
  │      ↓ emit topic.approved
  ├─→ ResearchProvider.run_research()
  │      ↓ emit research.completed
  ├─→ WritingProvider.write_article() [or parallel_draft for A/B]
  │      ↓ emit draft.ready
  ├─→ ComplianceProvider.check()
  ├─→ ComplianceProvider.approve()
  ├─→ ImageProvider.generate_images()
  └─→ PublishProvider.publish()
         ↓ emit article.published
```

### Monorepo 结构

```
packages/
├── core/          核心运行时（模型、事件、租户）
├── sdk/           平台 SDK（SPI、注册表、A/B 测试）
├── server/        HTTP 服务 + Web UI
├── cli/           命令行工具
├── domains/       领域组件
│   ├── topic/
│   ├── research/
│   ├── writing/
│   ├── compliance/  (18 项合规检查)
│   ├── image/
│   └── publish/
├── adapters/      外部集成
│   ├── tushare/     (A 股数据 · myMCP 兼容)
│   ├── cninfo/      (公告数据)
│   ├── wechat/      (微信发布)
│   ├── bibigpt/     (视频/音频摘要)
│   ├── minimax/     (妙想 · 多模态生成)
│   ├── datapro/     (专业搜索)
│   ├── bilibili/    (B站字幕/弹幕/动态/充电问答)
│   ├── trendradar/  (RSS 热点聚合 · 47 源)
│   └── knowledge/   (RAG 知识库检索)
└── editors/       编辑组件
    ├── yan-su-pai/  (严肃派)
    └── xi-li-pai/   (犀利派)
```

---

## HTTP API 参考

Base URL: `http://localhost:8000`

### 健康检查

```http
GET /health

{
  "status": "healthy",
  "version": "0.3.0",
  "components": {
    "data_sources": ["cninfo", "tushare"],
    "editors": ["yan-su-pai", "xi-li-pai"],
    "compliance": ["default"],
    "publishers": ["wechat"]
  }
}
```

### 租户管理

```http
POST /tenants
Content-Type: application/json

{
  "name": "我的投研团队"
}

→ {
  "tenant_id": "abc-123-...",
  "name": "我的投研团队",
  "slug": "tenant-7fffaa11"
}
```

```http
GET /tenants

→ {
  "total": 1,
  "tenants": [
    {"tenant_id": "...", "name": "我的投研团队", "slug": "tenant-..."}
  ]
}
```

### 文章生产

```http
POST /runs
Content-Type: application/json

{
  "tenant_name": "我的投研团队",
  "topic_title": "AI Agent 深度报告",      # 可选（不填则自动选题）
  "editor_slug": "yan-su-pai",           # 可选（不填则自动选择）
  "ab_test": false                        # 可选：true 启用 A/B 测试
}

→ {
  "run_id": "uuid-...",
  "tenant_id": "uuid-...",
  "status": "completed",
  "topic_title": "AI Agent 深度报告",
  "editor_slug": "yan-su-pai",
  "draft_length": 8523,
  "compliance_passed": true,
  "publish_url": "https://mp.weixin.qq.com/s/...",
  "ab_test_results": [...]   # 仅 ab_test=true 时
}
```

```http
GET /runs?tenant_id=<uuid>

→ {
  "total": 5,
  "runs": [
    {"run_id": "...", "status": "completed", ...}
  ]
}
```

```http
GET /runs/<run_id>

→ {完整的运行记录}
```

### 指标与监控

```http
GET /metrics

→ {
  "counters": {
    "workflow.runs.total{editor=yan-su-pai,status=completed}": 5
  },
  "gauges": {},
  "histograms": {
    "workflow.runs.duration": {
      "count": 5,
      "sum": 12.5,
      "avg": 2.5
    }
  }
}
```

### Web UI

```http
GET /

→ HTML 管理后台页面
```

---

## CLI 命令参考

```bash
# 显示帮助
uv run cf --help

# 健康检查
uv run cf health

# 创建文章
uv run cf create --tenant "我的团队" --topic "AI Agent" --editor yan-su-pai

# 列出所有运行
uv run cf list

# 查看运行详情
uv run cf status <run_id>

# 列出已注册组件
uv run cf components
```

---

## 核心概念详解

### 1. 组件（Component）

每个功能模块都是独立组件，通过 Python entry point 自动发现和注册。

#### 创建组件的步骤

1. 在 `packages/adapters/<name>/` 创建包
2. 实现 SPI 接口（`DataSourceProvider` / `EditorProvider` / `ComplianceProvider` / `PublisherProvider`）
3. 在 `pyproject.toml` 中声明 entry point
4. 运行 `uv sync` 即可自动注册

示例 entry point：

```toml
[project.entry-points."content_factory.data_sources"]
my_data = "content_factory_mydata:MyDataSource"
```

### 2. 事件（Event）

组件之间通过事件解耦通信。所有事件继承自 `DomainEvent`：

| 事件 | 触发时机 |
|---|---|
| `TopicApproved` | 选题被批准 |
| `ResearchCompleted` | 研究完成 |
| `DraftReady` | 草稿就绪 |
| `CompliancePassed` | 合规检查通过 |
| `ArticlePublished` | 文章发布 |

### 3. 租户（Tenant）

多租户数据隔离，每个租户有独立的数据空间：

- **内存后端**（默认）：dict 按 `tenant_id` 分隔
- **PostgreSQL 后端**：每租户独立 schema（`tenant_{slug}`）

### 4. 编辑风格（Editor Style）

每个编辑通过**风格指纹**量化其写作风格：

| 字段 | 含义 | 示例 |
|---|---|---|
| `formality` | 正式度 (0-1) | 严肃派 0.9 / 犀利派 0.3 |
| `risk_tolerance` | 风险容忍度 (0-1) | 严肃派 0.3 / 犀利派 0.8 |
| `vocabulary` | 常用词汇 | ["值得注意的是", "从数据来看"] |

---

## 多租户管理

### 内存后端（开发模式）

```python
from content_factory_core import create_tenant_manager

manager = create_tenant_manager("memory")

tenant = manager.create_tenant("我的团队", "my-team")
print(tenant.id)  # UUID
```

### PostgreSQL 后端（生产模式）

```bash
# 1. 安装依赖
pip install 'psycopg[binary]'

# 2. 设置数据库连接
export CF_DATABASE_URL="postgresql://user:pass@localhost:5432/content_factory"

# 3. 启动服务（自动使用 PostgreSQL 后端）
uv run uvicorn content_factory_server.app:app
```

PostgreSQL 后端会：
- 为每个租户创建独立 schema `tenant_{slug}`
- 在 schema 内创建 `runs` 和 `articles` 表
- 双写（内存缓存 + PostgreSQL）保证可用性
- PostgreSQL 写入失败时自动降级到内存

### 查询租户数据

```python
# 列出所有租户
tenants = manager.list_tenants()

# 获取某租户的运行记录
runs = manager.get_runs(tenant.id)

# 获取某租户的文章
articles = manager.get_articles(tenant.id)
```

---

## 文章生产工作流

完整工作流包含 5 个阶段：

### 阶段 1：选题（Topic）

```python
from content_factory_topic import TopicProvider

provider = TopicProvider(event_bus=event_bus)
topics = await provider.discover_topics(context)
await provider.approve_topic(topics[0], context)
```

### 阶段 2：研究（Research）

```python
from content_factory_research import DefaultResearchProvider
from content_factory_tushare import TushareDataSource

research = DefaultResearchProvider(
    data_sources=[TushareDataSource()],
    event_bus=event_bus,
)
await research.run_research(topic, context)
```

### 阶段 3：写作（Writing）

```python
from content_factory_writing import WritingProvider

writing = WritingProvider(registry=registry, event_bus=event_bus)
draft = await writing.write_article(topic, "yan-su-pai", context)
```

### 阶段 4：合规检查（Compliance）

```python
from content_factory_compliance import DefaultComplianceProvider

compliance = DefaultComplianceProvider()
result = await compliance.check(draft)
# result = {"passed": bool, "issues": [...], "risk_level": str}

article = await compliance.approve(draft)
```

### 阶段 5：发布（Publish）

```python
from content_factory_publish import PublishProvider
from content_factory_wechat import WechatPublisher

publish = WechatPublisher()
event = await publish.publish(article)
print(event.publish_url)
```

---

## 多编辑风格与 A/B 测试

### 使用单个编辑

```bash
curl -X POST http://localhost:8000/runs \
  -d '{"tenant_name": "我的团队", "topic_title": "...", "editor_slug": "yan-su-pai"}'
```

### A/B 测试（多编辑并行产出）

```bash
curl -X POST http://localhost:8000/runs \
  -d '{"tenant_name": "我的团队", "topic_title": "...", "ab_test": true}'
```

响应包含所有编辑的产出：

```json
{
  "run_id": "...",
  "editor_slug": "yan-su-pai",
  "ab_test_results": [
    {
      "editor": "yan-su-pai",
      "status": "success",
      "draft_id": "uuid-...",
      "content": "...",
      "length": 8523
    },
    {
      "editor": "xi-li-pai",
      "status": "success",
      "draft_id": "uuid-...",
      "content": "...",
      "length": 4567
    }
  ]
}
```

### 风格指纹匹配

```python
from content_factory_sdk.ab_testing import match_editor_for_topic

# 为话题匹配最佳编辑
matches = match_editor_for_topic(
    topic,
    editors=[editor1, editor2],
    preference={"formality": 0.8, "risk_tolerance": 0.4},
)
# matches = [(editor, distance), ...] 按匹配度排序
```

### 数据回流跟踪

```python
from content_factory_sdk.ab_testing import get_feedback_tracker

tracker = get_feedback_tracker()
tracker.record_feedback(article_id, {
    "read_count": 10000,
    "share_count": 234,
    "like_count": 567,
})
stats = tracker.aggregate_by_editor("yan-su-pai")
```

---

## 合规检查

### 18 项检查清单

| ID | 类别 | 检查项 |
|---|---|---|
| A1 | 标题 | 标题含反共识钩子 |
| A2 | 内容 | 候选公司 ≥ 18 家（行业类）|
| A3 | 数据 | 弱故事都有 Tickers |
| A4 | 结构 | Top 7 含 5 要素 |
| A5 | 论证 | 共识/分歧论证 |
| A6 | 配图 | 配图 ≥ 5 张 |
| A7 | 时效 | 数据时效（30 天内）|
| A8 | 法律 | 免责条款 |
| A9 | 证据 | 强弱证据 🟢🟡🔴 齐 |
| A10 | 来源 | 数据源 ≥ 10 个 |
| A11 | 风险 | 高风险词 0 误用 |
| A12 | 时效 | 时效窗口（H1 2026）|
| A13 | 评级 | 升降级信号 |
| A14 | 追踪 | 追踪记录 |
| A15 | 引用 | 访谈引用 |
| A16 | 验证 | verified_sources + verified_at |
| A17 | 报告 | research-reports 引用 |
| A17b | 爬虫 | ZsxqCrawler 引用 |
| C15 | 合规 | 综合合规检查 |

### 合规检查结果

```json
{
  "passed": true,
  "risk_level": "low",
  "issues": [
    {"id": "A6", "status": "WARN", "message": "配图数量 4，建议 ≥ 5"}
  ],
  "summary": "17/18 通过，1 个警告"
}
```

---

## 微信公众号发布

### 配置

```bash
export CF_WECHAT_APPID="wx1234567890abcdef"
export CF_WECHAT_SECRET="your_secret_here"
```

### 发布流程

```python
from content_factory_wechat import WechatPublisher

publisher = WechatPublisher()

# 1. 自动获取 access_token（带 7000 秒缓存）
# 2. 上传图文素材（uploadnews）
# 3. 发布草稿（freepublish/submit）
event = await publisher.publish(article)

print(event.publish_url)  # https://mp.weixin.qq.com/s/<publish_id>
```

### Mock 模式

未配置 `CF_WECHAT_APPID` / `CF_WECHAT_SECRET` 时，自动使用 mock 模式，返回假 URL：

```python
publisher = WechatPublisher()
# [warning] wechat_no_credentials msg='未配置 CF_WECHAT_APPID/CF_WECHAT_SECRET，使用 mock 模式'
publisher.is_mock  # True
```

---

## 外部数据源与知识库

除内置的 Tushare / 巨潮外，平台还提供 3 个外部集成适配器：**B站一手资料**、**TrendRadar RSS 热点**、**RAG 知识库**。三者都通过 entry point 自动注册，符合 SPI 协议。

### B站一手资料（bilibili）

把本地 `bilibili_toolkit` FastAPI 服务封装为 `DataSourceProvider`，获取字幕/弹幕/UP主动态/充电问答。

**前置依赖**：先启动 B站工具服务：

```bash
cd /Users/chenlei/002_tools/bilibili-subtitle-downloader
uvicorn bilibili_toolkit.server:app --host 127.0.0.1 --port 8100
```

**用法**：

```python
from content_factory_bilibili import BilibiliDataSource

bili = BilibiliDataSource()  # 默认读 CF_BILIBILI_URL=http://127.0.0.1:8100

# 字幕 markdown
r = await bili.fetch_video_subtitle("BV1xx411c7mD")

# 弹幕
dm = await bili.fetch_danmaku("BV1xx411c7mD")

# UP主动态 / 充电问答
dynamics = await bili.fetch_up_dynamics("12345678")
qa = await bili.fetch_qa("12345678")
```

> 字幕/弹幕是异步任务，适配器会自动轮询 `/api/task/{id}` 直到完成。

### TrendRadar RSS 热点（trendradar）

直读 TrendRadar 项目的 SQLite 输出（`output/rss/YYYY-MM-DD.db`），覆盖 47 个 RSS 源（财联社、华尔街见闻、36氪、界面、cnBeta…）。无需 TrendRadar 服务运行，只需本地 SQLite 存在。

**用法**：

```python
from content_factory_trendradar import TrendRadarDataSource

tr = TrendRadarDataSource()

# AI 风格热点聚合：从所有 RSS 源中筛出与 topic 相关的条目
hits = await tr.fetch_trending("AI Agent 行业", days=3, limit=20)

# 单源最近 N 天
items = await tr.fetch_rss("cls-telegraph", days=1)

# 订阅源清单
sources = await tr.list_sources()

# 单日摘要（类日报）
summary = await tr.daily_summary()
```

> 打分规则：标题命中 ×2、摘要命中 ×1；6 小时内 +3、24 小时内 +1.5。

### RAG 知识库（knowledge）

HTTP 客户端调用 `workspace/knowledge/knowledge-base` 的 RAG API，对内部知识库做语义检索。

**前置依赖**：

```bash
cd /Users/chenlei/workspace/knowledge/knowledge-base
source .venv/bin/activate
uvicorn api:app --host 127.0.0.1 --port 8002
```

**用法**：

```python
from content_factory_knowledge import KnowledgeSearchProvider

kb = KnowledgeSearchProvider()  # 默认 CF_KNOWLEDGE_URL=http://127.0.0.1:8002

# 语义检索：hybrid / mmr / vector / bm25
r = await kb.search("什么是 Alpha 因子", domain="hybrid", limit=10)
for doc in r["results"]:
    print(doc["title"], doc["score"])

# RAG 完整链路：检索 + LLM 生成回答
answer = await kb.query_with_answer("什么是 Alpha 因子")
print(answer["answer"])
```

### 环境变量一览

| 变量 | 默认值 | 说明 |
|---|---|---|
| `CF_BILIBILI_URL` | `http://127.0.0.1:8100` | B站工具服务地址 |
| `CF_BILIBILI_API_KEY` | - | B站 API Key（可选） |
| `CF_TRENDRADAR_DB_DIR` | `/Users/chenlei/001_project/TrendRadar/output/rss` | SQLite 目录 |
| `CF_KNOWLEDGE_URL` | `http://127.0.0.1:8002` | 知识库 RAG API 地址 |

---

## 可观测性

### OpenTelemetry

默认启用真实的 OpenTelemetry `TracerProvider`：

```python
from content_factory_server.observability import init_tracing, trace_span

init_tracing("my-service")

with trace_span("workflow.run", {"tenant_id": "..."}):
    # 你的代码
    pass
```

### 控制台导出（调试）

```bash
export CF_TRACE_CONSOLE=1
uv run uvicorn content_factory_server.app:app
```

控制台会打印 JSON 格式的 span：

```json
{
  "name": "workflow.run",
  "context": {
    "trace_id": "0x722530b2d7162ed3d612a658e9ad8ae9",
    "span_id": "0x..."
  },
  "attributes": {"tenant_id": "..."}
}
```

### 指标收集

```python
from content_factory_server.observability import metrics

# 计数器
metrics.increment("workflow.runs.total", labels={"editor": "yan-su-pai"})

# 仪表
metrics.gauge("active_tenants", 5)

# 直方图
metrics.observe("workflow.runs.duration", 2.5, labels={"tenant": "..."})

# 获取快照
snapshot = metrics.snapshot()
```

访问 `GET /metrics` 端点即可获取快照。

---

## Temporal 编排

### 启动 Temporal Server

```bash
docker-compose -f docker-compose.temporal.yml up -d
```

服务：
- Temporal gRPC: `localhost:7233`
- Temporal Web UI: `http://localhost:8080`

### 工作流定义

```python
from content_factory_server.temporal_workflows import (
    ArticleProductionWorkflow,
    ArticleProductionInput,
)

input = ArticleProductionInput(
    tenant_id="uuid-...",
    topic_title="AI Agent 深度报告",
    editor_slug="yan-su-pai",
    require_manual_approval=True,  # 启用人工审批
)
```

### Activity 重试策略

| Activity | 超时 | 重试 |
|---|---|---|
| 选题 | 5 分钟 | 3 次 |
| 研究 | 30 分钟 | 2 次 |
| 写作 | 15 分钟 | 默认 |
| 合规 | 5 分钟 | 1 次（不重试）|
| 发布 | 10 分钟 | 5 次 |

### 人工审批（Signal）

```python
# 工作流等待审批
await workflow.wait_condition(lambda: approval_granted)

# 通过 Signal 触发
await client.signal_workflow(workflow_id, "grant_approval")
await client.signal_workflow(workflow_id, "reject_approval")
```

### 进度查询（Query）

```python
progress = await client.query_workflow(workflow_id, "get_progress")  # 0-100
status = await client.query_workflow(workflow_id, "get_status")
current = await client.query_workflow(workflow_id, "get_current_activity")
```

---

## Web UI 管理后台

访问 `http://localhost:8000/` 即可看到：

- **统计卡片** — 租户数 / 组件数 / 运行数 / 版本
- **组件列表** — 已注册的所有组件类型和数量
- **租户表** — 租户名称、slug、运行数
- **API 文档** — 所有端点的快速参考

纯 HTML/CSS 实现，无外部依赖，移动端可访问。

---

## 开发新组件

### 示例：创建新的数据源

**步骤 1：创建包结构**

```bash
mkdir -p packages/adapters/wind/content_factory_wind
cd packages/adapters/wind
```

**步骤 2：编写 `pyproject.toml`**

```toml
[project]
name = "content-factory-wind"
version = "0.1.0"
description = "Wind 数据源适配器"
requires-python = ">=3.11"
readme = "README.md"
dependencies = ["content-factory-sdk", "WindPy"]

[tool.uv.sources]
content-factory-sdk = { workspace = true }

[project.entry-points."content_factory.data_sources"]
wind = "content_factory_wind:WindDataSource"
```

**步骤 3：实现 SPI**

```python
# content_factory_wind/__init__.py
from content_factory_sdk.spi import DataSourceProvider

class WindDataSource(DataSourceProvider):
    async def fetch_stock_data(self, symbol: str) -> dict:
        # 调用 Wind API
        ...

    async def fetch_news(self, query: str, limit: int = 10) -> list[dict]:
        ...

    async def fetch_announcement(self, symbol: str, days: int = 30) -> list[dict]:
        ...
```

**步骤 4：同步并验证**

```bash
uv sync --all-packages
uv run cf components  # 应该看到 wind 出现在 data_sources
```

### SPI 接口参考

| 接口 | 方法 |
|---|---|
| `DataSourceProvider` | `fetch_stock_data`, `fetch_news`, `fetch_announcement` |
| `EditorProvider` | `draft_article`, `style_fingerprint`, `can_handle` |
| `ComplianceProvider` | `check`, `approve` |
| `PublisherProvider` | `publish` → `ArticlePublished \| dict` |

---

## 生产部署

### Docker Compose 全栈部署

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - CF_TUSHARE_TOKEN=${CF_TUSHARE_TOKEN}
      - CF_WECHAT_APPID=${CF_WECHAT_APPID}
      - CF_WECHAT_SECRET=${CF_WECHAT_SECRET}
      - CF_DATABASE_URL=postgresql://user:pass@db/content_factory
    depends_on:
      - db
      - temporal

  db:
    image: postgres:16
    environment:
      POSTGRES_DB: content_factory
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes:
      - pg-data:/var/lib/postgresql/data

  temporal:
    image: temporalio/auto-setup:latest
    ports:
      - "7233:7233"
    environment:
      - DB=postgresql
      - DB_PORT=5432
      - POSTGRES_USER=user
      - POSTGRES_PWD=pass
      - POSTGRES_SEEDS=db
    depends_on:
      - db

  temporal-web:
    image: temporalio/ui:latest
    ports:
      - "8080:8080"
    environment:
      - TEMPORAL_ADDRESS=temporal:7233

volumes:
  pg-data:
```

### 环境变量清单

```bash
# 数据源
export CF_TUSHARE_TOKEN="your_token"                     # Tushare（或 myMCP 兼容 token）
export CF_TUSHARE_BASE_URL="https://tt.xiaodefa.cn/..."  # myMCP 兼容后端（可选，覆盖 Tushare）
export CF_BIBIGPT_TOKEN="your_token"                     # BibiGPT 视频/音频摘要

# 多模态生成
export CF_MINIMAX_API_KEY="your_key"                     # MiniMax (妙想) API
export CF_MINIMAX_GROUP_ID="your_group_id"

# 专业搜索
export CF_DATAPRO_TOKEN="your_token"                     # dataPro（学术/工商/风险/股票/新闻）

# 外部数据源与知识库
export CF_BILIBILI_URL="http://127.0.0.1:8100"           # B站工具服务（bilibili_toolkit）
export CF_TRENDRADAR_DB_DIR="/path/to/TrendRadar/output/rss"  # TrendRadar SQLite 目录
export CF_KNOWLEDGE_URL="http://127.0.0.1:8002"          # RAG 知识库 API

# 发布
export CF_WECHAT_APPID="wx..."                           # 微信公众号
export CF_WECHAT_SECRET="..."

# 数据库
export CF_DATABASE_URL="postgresql://user:pass@localhost/content_factory"

# 调试
export CF_TRACE_CONSOLE=1                                # OpenTelemetry 控制台
```

### 监控建议

1. **OpenTelemetry** → Jaeger/Tempo（span 追踪）
2. **/metrics** → Prometheus + Grafana（指标监控）
3. **Temporal Web UI**（http://localhost:8080）— 工作流可视化
4. **PostgreSQL** — pg_stat_activity / slow query log

---

## 故障排查

### 常见问题

**Q: 启动服务时报错 `ModuleNotFoundError: content_factory_xxx`**

```bash
# 重新同步工作区
uv sync --all-packages --reinstall
```

**Q: CLI 无法连接服务**

```bash
# 检查服务是否运行
curl http://localhost:8000/health

# 检查 SOCKS 代理问题
unset http_proxy https_proxy all_proxy
```

**Q: 微信公众号发布失败**

```bash
# 检查环境变量
echo $CF_WECHAT_APPID
echo $CF_WECHAT_SECRET

# 检查 mock 模式
uv run python -c "from content_factory_wechat import WechatPublisher; print(WechatPublisher().is_mock)"
```

**Q: 合规检查返回 FAIL**

```bash
# 查看详细问题
uv run python -c "
from content_factory_compliance import DefaultComplianceProvider
# ... 查看 result['issues']
"
```

**Q: 测试失败**

```bash
# 运行特定测试
uv run pytest test_api.py -v

# 查看完整输出
uv run pytest test_smoke.py -s
```

### 日志级别

```bash
# 设置日志级别
export LOG_LEVEL=DEBUG  # 调试
export LOG_LEVEL=INFO   # 正常
export LOG_LEVEL=WARNING  # 精简
```

---

## 附录

### 测试套件

| 测试文件 | 覆盖范围 |
|---|---|
| `test_smoke.py` | 组件发现 / 事件总线 / 合规 / 编辑 / 数据源 / 完整工作流 |
| `test_e2e.py` | 端到端工作流 |
| `test_api.py` | HTTP API 端点 |
| `test_cli.py` | CLI 命令 |
| `test_multi_editor.py` | 多编辑风格 |

### 版本历史

详见 [CHANGELOG.md](../CHANGELOG.md)

### 贡献指南

详见 [CONTRIBUTING.md](../CONTRIBUTING.md)
