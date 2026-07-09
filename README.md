# content-factory

> **A 股投研深度文的生产基础设施** — 17 步 SOP · 18 项合规硬约束 · 三源数据闭环
>
> 让 AI 用你自己的方法论可靠地产出合规的投研深度文（8000-10000 字），从选题到一键发布公众号。

[![CI](https://img.shields.io/badge/ci-passing-brightgreen.svg)](https://github.com/lululu811/content-factory/actions)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![uv](https://img.shields.io/badge/uv-workspace-purple.svg)](https://docs.astral.sh/uv/)
[![Tushare](https://img.shields.io/badge/Tushare-compatible-blue.svg)](https://tushare.pro)
[![WeChat](https://img.shields.io/badge/微信公众号-API_集成-green.svg)](https://mp.weixin.qq.com)

---

## 你能用它解决什么问题

| 你遇到的问题 | content-factory 怎么帮 |
|---|---|
| 每篇深度文从选题到发布要一整天 | 17 步 SOP 把流程拆成 Python 流水线（`bin/cf-new.sh` 一键跑完） |
| 合规红线踩一条就翻车 | 18 项硬约束 `compliance check` 发布前自动门禁，FAIL 直接拒绝 |
| 数据源分散（公告 / 行情 / 财报 / RSS / 音视频）| 三源闭环：TrendRadar（选题）+ Tushare / 巨潮（硬数据）+ ZsxqCrawler（机构观点） |
| AI 写出的东西踩红字词 / 缺免责 | 多编辑风格"严肃派/犀利派"风格指纹 + A/B 测试，发布前合规二次扫描 |
| 多团队 / 多账号协作 | Schema 级 PostgreSQL 多租户 + 内存后端（开发模式） |

---

## 30 秒体验

```bash
# 1. clone + 同步(uv workspace 单命令)
git clone https://github.com/lululu811/content-factory.git
cd content-factory
uv sync --all-packages --dev

# 2. 自检
uv run cf health          # 探活 + 列已注册组件

# 3. 跑一篇端到端 mock 文章(无需任何 API token)
uv run cf create "我的团队" --topic "AI Agent 行业深度报告"

# 4. 启动 HTTP 服务(管理后台 + REST API)
uv run cf-server
# 访问 http://localhost:8000/ 看 Dashboard
```

未配置 `CF_TUSHARE_TOKEN` / `CF_WECHAT_APPID` 等 token 时，所有外部依赖**自动降级为 mock 模式**，不会报错。完整 `examples/` 见 [examples/](examples/)。

---

## ✨ 特性

- **🧩 组件化架构** — 每个能力（数据源 / 编辑 / 合规 / 发布）都是独立组件，通过 entry point 自动注册
- **👥 多编辑风格** — 内置"严肃派""犀利派"等 AI 编辑，支持 A/B 测试并行产出
- **🏢 多租户隔离** — Schema-level 隔离（PostgreSQL）+ 内存后端（开发模式）
- **🔍 18 项合规检查** — 覆盖标题/数据/免责/时效/引用等全维度
- **📊 真实数据源** — Tushare（行情/新闻）+ 巨潮（公告）+ TrendRadar（50 个 RSS 源）+ B 站 + 知识库 RAG
- **📺 B站一手资料** — 字幕/弹幕/UP主动态/充电问答（本地 bilibili_toolkit 服务）
- **📡 RSS 热点聚合** — TrendRadar SQLite 直读，AI 风格热点筛选
- **🧠 知识库 RAG** — hybrid/mmr/vector/bm25 多模式语义检索
- **📤 微信发布** — 微信公众号 API 直接集成（access_token 缓存 + 图文上传 + 发布）
- **🎬 BibiGPT 集成** — 任意视频/音频 URL 一键转结构化摘要
- **🎨 妙想 (MiniMax) 集成** — 图片/视频/音乐/语音多模态生成
- **🔎 dataPro 集成** — 学术/工商/风险/股票/新闻专业检索
- **🔭 OpenTelemetry** — 真实追踪（trace_id）+ 指标收集（counters / gauges / histograms）
- **⏱️ Temporal 编排** — 文章生产工作流（6 Activity + Signal + Query）
- **🌐 Web 管理后台** — 单页 Dashboard，零依赖
- **⚡ FastAPI HTTP API** — RESTful 接口，支持所有功能

## 🏗️ 架构

```
┌─────────────────────────────────────────────────────────────┐
│                       Applications                           │
│   CLI (cf)  ·  FastAPI HTTP  ·  Web UI Dashboard             │
├─────────────────────────────────────────────────────────────┤
│                       Orchestration                          │
│   Temporal Workflow  ·  Event Bus  ·  A/B Testing             │
├─────────────────────────────────────────────────────────────┤
│                        Components                            │
│  topic · research · writing · compliance · image · publish  │
│  yan-su-pai · xi-li-pai · tushare · cninfo · wechat         │
│  bibigpt · minimax · datapro · bilibili · trendradar        │
│  knowledge (RAG)                                            │
├─────────────────────────────────────────────────────────────┤
│                         Platform                             │
│   Core Models · SDK SPI · Registry · OpenTelemetry          │
│   TenantManager (Memory / PostgreSQL)                       │
└─────────────────────────────────────────────────────────────┘
```

详细架构决策见 [docs/adr/001-component-based-architecture.md](docs/adr/001-component-based-architecture.md)

## 📦 包结构

```
packages/
├── core/                         # 核心运行时：模型、事件、配置、租户管理
├── sdk/                          # SDK：SPI 接口、事件总线、组件注册、A/B 测试
├── server/                       # FastAPI HTTP 服务 + Web UI
├── cli/                          # CLI 工具（cf 命令）
├── domains/                      # 领域组件
│   ├── topic/                    # 选题
│   ├── research/                 # 研究
│   ├── writing/                  # 写作
│   ├── compliance/               # 合规（18 项）
│   ├── image/                    # 配图
│   └── publish/                  # 发布
├── adapters/                     # 外部集成
│   ├── tushare/                  # Tushare 数据源（支持 myMCP 后端）
│   ├── cninfo/                   # 巨潮数据源
│   ├── wechat/                   # 微信公众号发布
│   ├── bibigpt/                  # BibiGPT 视频/音频摘要
│   ├── minimax/                  # MiniMax (妙想) 多模态生成
│   ├── datapro/                  # dataPro 专业数据检索
│   ├── bilibili/                 # B站字幕/弹幕/动态/充电问答
│   ├── trendradar/               # TrendRadar RSS 热点聚合
│   └── knowledge/                # RAG 知识库语义检索
└── editors/                      # 编辑组件
    ├── yan-su-pai/               # 严肃派（formality=0.9）
    └── xi-li-pai/                # 犀利派（formality=0.3）
```

## 🚀 快速开始

### 1. 安装

```bash
# 克隆仓库
git clone https://github.com/lululu811/content-factory.git
cd content-factory

# 同步所有包（使用 uv）
uv sync --all-packages
```

### 2. 启动 HTTP 服务

```bash
# 启动服务（默认 http://localhost:8000）
uv run uvicorn content_factory_server.app:app --reload

# 或者通过 CLI 启动
uv run cf-server
```

访问：
- API 文档：http://localhost:8000/docs
- 管理后台：http://localhost:8000/
- 健康检查：http://localhost:8000/health
- 指标：http://localhost:8000/metrics

### 3. CLI 快速使用

```bash
# 查看组件
uv run cf components

# 创建一篇新文章
uv run cf create --tenant "测试租户" --topic "AI Agent 行业深度报告"

# 列出运行记录
uv run cf list

# 查看运行详情
uv run cf status <run_id>
```

### 4. HTTP API 使用

```bash
# 健康检查
curl http://localhost:8000/health

# 创建租户
curl -X POST http://localhost:8000/tenants \
  -H "Content-Type: application/json" \
  -d '{"name": "我的投研团队"}'

# 创建文章（单编辑）
curl -X POST http://localhost:8000/runs \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_name": "我的投研团队",
    "topic_title": "AI Agent 行业深度报告",
    "editor_slug": "yan-su-pai"
  }'

# 创建文章（A/B 测试 - 多编辑并行产出）
curl -X POST http://localhost:8000/runs \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_name": "我的投研团队",
    "topic_title": "AI Agent 行业深度报告",
    "ab_test": true
  }'
```

## 📖 文档

- **[使用手册](docs/user-guide.md)** — API 参考 / 多租户 / 开发新组件 / 生产部署
- **[架构决策](docs/adr/001-component-based-architecture.md)** — 为什么组件化 / Temporal / schema-level 隔离
- **[SOP](SOP.md)** — 17 步文章生产 SOP
- **[数据源层级](docs/data-source-hierarchy.md)** — 主要 / 验证 / 理论支撑 三类
- **[公众号样式指南](docs/cn-pub-style-guide.md)** — Markdown → 公众号的翻译损失与 10 条规则
- **[AI interests 映射](docs/ai-interests-mapping.md)** — TrendRadar 15 类兴趣 × 9 大主题
- **[鲁班工坊打磨报告](docs/luban-reports/content-factory-review-2026-07-05.md)** — 65→78 分提升路径
- **[整改清单](TODO.md)** — 已完成项 + 下一步迭代
- **[安全策略](SECURITY.md)** — 支持版本矩阵 + 漏洞报告渠道
- **[示例](examples/)** — 端到端 quickstart 脚本

## 🧪 测试

```bash
# 运行所有测试
uv run pytest

# 运行特定测试套件
uv run pytest test_smoke.py test_e2e.py test_api.py test_cli.py test_multi_editor.py

# 带覆盖率
uv run pytest --cov=content_factory_server --cov-report=term-missing
```

## 🔌 环境变量

| 变量名 | 必需 | 说明 |
|---|---|---|
| `CF_TUSHARE_TOKEN` | 否 | Tushare API token（未配置时使用 mock） |
| `CF_TUSHARE_BASE_URL` | 否 | myMCP 兼容端点（如 `https://<your-myMCP-host>/mcp/token=<your-token>`） |
| `CF_BIBIGPT_TOKEN` | 否 | BibiGPT API token（视频/音频摘要） |
| `CF_MINIMAX_API_KEY` | 否 | MiniMax (妙想) API key（图片/视频/音乐/语音） |
| `CF_MINIMAX_GROUP_ID` | 否 | MiniMax Group ID |
| `CF_DATAPRO_TOKEN` | 否 | dataPro 专业搜索 token（学术/工商/风险/股票） |
| `CF_BILIBILI_URL` | 否 | B站工具服务地址（默认 `http://127.0.0.1:8100`） |
| `CF_BILIBILI_API_KEY` | 否 | B站工具 API Key（可选） |
| `CF_TRENDRADAR_DB_DIR` | 否 | TrendRadar SQLite 目录（默认 `/Users/chenlei/001_project/TrendRadar/output/rss`） |
| `CF_KNOWLEDGE_URL` | 否 | 知识库 RAG API 地址（默认 `http://127.0.0.1:8002`） |
| `CF_WECHAT_APPID` | 否 | 微信公众号 AppID（未配置时使用 mock） |
| `CF_WECHAT_SECRET` | 否 | 微信公众号 Secret |
| `CF_DATABASE_URL` | 否 | PostgreSQL 连接串（未配置时使用内存后端） |
| `CF_TRACE_CONSOLE` | 否 | 设为 `1` 开启 OpenTelemetry 控制台输出 |

## 🎯 核心概念

### 1. 组件（Component）

每个功能模块都是独立组件，通过 Python entry point 自动注册：

```toml
# packages/adapters/wechat/pyproject.toml
[project.entry-points."content_factory.publishers"]
wechat = "content_factory_wechat:WechatPublisher"
```

组件类型（SPI 接口）：
- `DataSourceProvider` — 数据源
- `EditorProvider` — 编辑
- `ComplianceProvider` — 合规检查
- `PublisherProvider` — 发布

### 2. 事件（Event）

组件之间通过事件解耦通信：

```
topic.approved → research.completed → draft.ready → article.published
```

### 3. 租户（Tenant）

多租户隔离，每个租户有独立的 schema（PostgreSQL）或命名空间（内存）：

```python
from content_factory_core import create_tenant_manager

# 自动选择后端
manager = create_tenant_manager("auto")
tenant = manager.create_tenant("我的团队", "my-team")
```

### 4. 编辑风格（Editor Style）

每个编辑有风格指纹（formality / risk_tolerance / vocabulary）：

```python
# 严肃派
formality=0.9, risk_tolerance=0.3
keywords: "值得注意的是", "从数据来看", "综上所述"

# 犀利派
formality=0.3, risk_tolerance=0.8
keywords: "说人话就是", "别装了", "醒醒吧"
```

## 📚 进阶主题

- **[开发新组件](docs/user-guide.md#开发新组件)** — 创建自定义数据源 / 编辑 / 合规 / 发布
- **[Temporal 工作流](docs/user-guide.md#temporal-编排)** — 启用工作流持久化 + 重试 + 人工审批
- **[生产部署](docs/user-guide.md#生产部署)** — Docker Compose + PostgreSQL + Temporal

## 🤝 贡献

欢迎贡献！详见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 📄 许可证

MIT License — 详见 [LICENSE](LICENSE)。

## ⚠️ 免责声明

`content-factory` 是内容生产工具，不构成投资建议。用户应独立判断所有投资决策。
