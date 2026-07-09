# content-factory · AI 编辑部

## 项目速览

`content-factory` 是**投研型公众号深度文 AI 编辑部操作系统** —— 一套组件化、多租户的端到端流水线,从 A 股投研数据的选题、合规,到多编辑风格 A/B 测试、微信公众号发布,全部由 Python 单语言实现并通过 entry point 自动组装。

核心定位与边界:

- **做什么**:把 A 股投研选题 → 研究 → 多风格写作 → 18 项合规 → 微信公众号发布做成可扩展流水线
- **不做什么**:不做证券研究本身、不构成投资建议(详见 README 免责声明)
- **目标用户**:投研型公众号主理人 / 个人投资者,以及需要在自家工作流里接入 A 股/合规/公众号发布的开发者
- **状态**:v0.3.0,首次 MIT 开源(2026-06-29),架构决策见 `docs/adr/001-component-based-architecture.md`

## 语言与排版约定

- **回复、注释、文档、commit 消息默认使用中文**,`commit` 标题使用 `<scope>: <subject>` 形式(scope 例:`SOP` / `scripts` / `docs` / `packages` / `compliance` / `data-source`)
- 遵循《中文文案排版指北》:中英文之间加空格,中文与数字之间加空格,中文标点使用全角,数字使用半角
- 中文引号默认使用全角直角引号「」
- 涉及股票代码、专有名词、品牌名时保留原始大小写与半角格式(如 `Tushare`、`BibiGPT`、`wechat`)
- 标识符(模块名、函数名、配置 key)统一使用英文/拼音,文件正文与 frontmatter 使用中文

## Monorepo 布局

整个工程是 **uv workspace** 多包结构,根 `pyproject.toml` 通过 `[tool.uv.workspace]` 聚合所有子包,统一锁文件 `uv.lock`。

```
content-factory/
├── packages/
│   ├── core/           # content-factory-core  核心运行时(领域模型、事件、配置、租户)
│   ├── sdk/            # content-factory-sdk   平台 SDK(SPI、事件总线、组件注册、A/B 测试)
│   ├── server/         # content-factory-server  FastAPI HTTP 服务 + Web UI + Temporal
│   ├── cli/            # content-factory-cli   typer 命令行(cf 命令)
│   ├── domains/        # 6 个领域组件,每包一个 Python 包
│   │   ├── topic/        # 选题发现 / 评分 / 批准
│   │   ├── research/     # 数据收集 / 行业扫描 / 事件
│   │   ├── writing/      # 编排编辑组件,生成草稿
│   │   ├── compliance/   # 18 项合规检查(A1-A17b + C15)
│   │   ├── image/        # 配图生成
│   │   └── publish/      # 抽象发布层(默认 mock)
│   ├── adapters/       # 9 个外部集成
│   │   ├── tushare/      # A 股行情/新闻/公告,支持 myMCP JSON-RPC 后端
│   │   ├── cninfo/       # 巨潮资讯公告
│   │   ├── wechat/       # 微信公众号 access_token + uploadnews + freepublish
│   │   ├── bibigpt/      # 视频/音频结构化摘要
│   │   ├── minimax/      # MiniMax(妙想)多模态生成
│   │   ├── datapro/      # 学术/工商/风险/股票/新闻专业搜索
│   │   ├── bilibili/     # B 站字幕/弹幕/动态/充电问答(对接外部 bilibili_toolkit)
│   │   ├── trendradar/   # 直读 TrendRadar SQLite,聚合 RSS 热点
│   │   └── knowledge/    # RAG 知识库 hybrid / mmr / vector / bm25
│   └── editors/        # 编辑风格组件
│       ├── yan-su-pai/   # 严肃派(formality=0.9, risk_tolerance=0.3)
│       └── xi-li-pai/    # 犀利派(formality=0.3, risk_tolerance=0.8)
├── docs/               # 用户手册、ADR、数据源层级说明、luban 报告
├── templates/          # 文章模板与合规模板(仅在 v0.2 旧脚本流中引用,新架构不强制)
├── scripts/            # 运维脚本(daily-feed / publish / quarterly-review / tracking-record 等)
├── bin/                # 一键发文脚本(cf-new / cf-new-stock / cninfo-pipeline)
├── drafts/             # 本地草稿,gitignored
├── publish/            # 发布包,gitignored
├── tracking/           # 跟踪表与战绩表,gitignored
├── archives/           # 归档,gitignored
├── test_*.py           # 6 个集成/冒烟测试(test_smoke / test_e2e / test_api / test_cli / test_multi_editor / test_compliance_migration)
├── pyproject.toml      # uv workspace + 共享 dev 依赖 + ruff/mypy/pytest 配置
├── uv.lock             # 全局锁文件
├── docker-compose.temporal.yml  # Temporal Server + UI + Worker
└── .github/workflows/ci.yml    # GitHub Actions:lint / test(3 OS × 3 Python) / build
```

> **重要**:根目录的 `00-规则与索引/` 等 `0X-` 数字前缀目录是早期 `dbs-content-system` 试错产物,已在 `.gitignore` 中标记为本地保留,本工程不再使用,不要新增文件到这些目录。

## 构建与运行

### 1. 环境要求

- **Python 3.11+**(CI 矩阵覆盖 3.11 / 3.12 / 3.13,与 `requires-python` 对齐)
- **uv**(强烈推荐,所有命令围绕 `uv sync` / `uv run` 设计)
- 可选:`temporalio`(`docker-compose up` 后才需要),`psycopg[binary]`(PostgreSQL 多租户),`tushare`(真实数据源)
- macOS / Linux 均可,CI 同时跑 windows-latest

### 2. 安装

```bash
git clone https://github.com/lululu811/content-factory.git
cd content-factory
uv sync --all-packages
```

这一步会同时安装根目录 `dev` 依赖组(`pytest` / `pytest-cov` / `pytest-asyncio` / `ruff` / `mypy`)和所有子包。

### 3. 启动 HTTP 服务

```bash
# 方式 A:直接 uvicorn
uv run uvicorn content_factory_server.app:app --reload

# 方式 B:用 cf-server 入口(等价)
uv run cf-server
```

启动后访问:

- API 文档:`http://localhost:8000/docs`
- Web 管理后台:`http://localhost:8000/`
- 健康检查:`http://localhost:8000/health`
- 指标:`http://localhost:8000/metrics`

### 4. CLI 快速使用

```bash
uv run cf health           # 探活 + 列组件
uv run cf components       # 按类别列出已注册组件
uv run cf create "我的团队" --topic "AI Agent 深度报告"           # 单编辑模式
uv run cf create "我的团队" --topic "AI Agent 深度报告" --editor xi-li-pai  # 指定编辑
uv run cf list             # 列出所有运行
uv run cf status <run_id>  # 查看单次运行详情
```

### 5. 启动 Temporal(可选,生产用)

```bash
docker-compose -f docker-compose.temporal.yml up -d
# UI: http://localhost:8080
# gRPC: localhost:7233
# 跑完记得 docker-compose down
```

`packages/server/content_factory_server/temporal_workflows.py` 已实现 6 Activity + Signal + Query,temporalio 未安装时优雅降级为占位。

## 关键架构

### 1. 组件模型(Entry Point 注册)

每个能力都是独立包,通过 Python entry point 暴露,运行时由 `content_factory_sdk.registry.discover_components()` 自动发现。**不要**在业务代码里直接 import 适配器,统一走 `registry.get_*()` 取。

| 组件类型 | SPI Protocol | Entry point group | 已注册实例 |
|---|---|---|---|
| 数据源 | `DataSourceProvider` | `content_factory.data_sources` | `tushare`, `cninfo`, `bibigpt`, `bilibili`, `trendradar` |
| 编辑 | `EditorProvider` | `content_factory.editors` | `yan-su-pai`, `xi-li-pai` |
| 合规 | `ComplianceProvider` | `content_factory.compliance` | `default` |
| 发布 | `PublisherProvider` | `content_factory.publishers` | `wechat`, `publish-stub` |
| 内容生成 | `ContentGeneratorProvider` | `content_factory.content_generators` | `minimax` |
| 专业搜索 | `SearchProvider` | `content_factory.search_providers` | `datapro`, `knowledge` |
| 领域(非 entry point) | 直接 import | — | `TopicProvider` / `ResearchProvider` / `WritingProvider` / `ComplianceProvider` / `ImageProvider` / `PublishProvider` |

新增组件的标准流程:

1. 在 `packages/adapters/<name>/` 新建子包,`pyproject.toml` 写 `[project.entry-points."content_factory.<group>"]`
2. 写 `content_factory_<name>/__init__.py` 实现对应 Protocol
3. `uv sync --all-packages` 让 entry point 重新生效
4. 在 `test_smoke.py` 或新增 `test_<name>.py` 中加组件发现断言

### 2. 事件流

跨领域通信走 `content_factory_sdk.events.EventBus`(`InMemoryEventBus` 是当前唯一实现)。事件类型全部在 `content_factory_core.events` 定义,继承 `DomainEvent`,`event_type` 用 `Literal` 锁定。

```
topic.approved → research.completed → draft.ready → (compliance.passed) → article.published
```

实现位置:

- `TopicProvider.approve_topic` 发出 `TopicApproved`
- `DefaultResearchProvider.run_research` 发出 `ResearchCompleted`
- `WritingProvider.write_article` 发出 `DraftReady`
- `PublishProvider.publish` 发出 `ArticlePublished`

### 3. 多租户

`content_factory_core.tenant_manager` 提供:

- `TenantManager` —— 内存后端,默认
- `PostgreSQLTenantManager` —— `CF_DATABASE_URL` 存在时启用,schema-level 隔离(`tenant_{slug}`),写入失败自动降级内存
- `create_tenant_manager(backend="auto")` —— 工厂函数,根据环境自动选择
- `get_tenant_manager()` —— 全局单例

`packages/server/content_factory_server/app.py` 在 `/tenants` 与 `/runs` 中使用,所有 run/article 记录按租户隔离。

### 4. 配置与可观测性

- 所有配置走 `pydantic_settings.BaseSettings`,统一 `CF_` 前缀环境变量(详见下表)
- `packages/server/content_factory_server/observability.py` 封装 OpenTelemetry,提供 `trace_span` 上下文管理器与 `Metrics` 收集器(counters / gauges / histograms),未安装 otel 时降级到 structlog + 内存指标
- `record_workflow_run` 集中记录 workflow 级指标,通过 `GET /metrics` 暴露快照

## 代码风格

根 `pyproject.toml` 已锁定工具链:

- **ruff** —— `line-length=100`,`target-version="py39"`,启用 `E/W/F/I/N/UP/B/C4/SIM/TCH`,`tests/**` 放开 `B011`,`legacy` 文件单独放开
- **mypy** —— 全工程 `strict=false`,`content_factory_cninfo.*` 单独 `strict=true`,`tests.*` 放开 `disallow_untyped_defs`
- **代码生成** —— 所有子包用 `hatchling` 后端,`packages = ["content_factory_xxx"]` 一致写法

写新包时:

- 包名遵循 `content-factory-<kebab-case>`(包名) → 导入名 `content_factory_<snake_case>` 的统一约定
- 所有公开类必须有 docstring(中文即可,简洁为先)
- Protocol 实现用 `@runtime_checkable`(参见 `content_factory_sdk.spi`)
- 异步 I/O 全部 `async/await`,HTTP 客户端用 `httpx.AsyncClient`,`trust_env=False` 绕过系统代理
- 日志统一用 `structlog.get_logger()`,事件类型作为 key(如 `event_emitted`, `wechat_token_refreshed`)
- mock 模式必须存在:任何外部依赖缺失/未配置时,组件要降级返回 mock 数据而不是抛异常

## 测试

### 运行测试

```bash
# 全部
uv run pytest

# 跑根目录的 6 个集成测试
uv run pytest test_smoke.py test_e2e.py test_api.py test_cli.py test_multi_editor.py test_compliance_migration.py

# 单测 + 覆盖率
uv run pytest --cov=content_factory_server --cov-report=term-missing
```

`pyproject.toml` 中 pytest 配置:

- `asyncio_mode = "auto"` —— 异步 fixture 无需显式装饰
- `addopts` 强制带 coverage(`--cov=content_factory`)
- `filterwarnings` 屏蔽 `pdfplumber` / `matplotlib` 的 DeprecationWarning
- 测试文件命名 `test_*.py`、类 `Test*`、函数 `test_*`

### 写测试时的注意点

- 根目录的 `test_*.py` 是**集成 / 冒烟测试**,文件顶部用 `import pytest` + `#!/usr/bin/env python3` 兼容 `python3 test_smoke.py` 直接跑
- 测组件发现时,断言 `tushare` / `yan-su-pai` / `default` 至少要存在
- 测事件总线时,断言 `received` 列表长度而非事件对象细节
- 测合规时构造最小可触发 fixture,关注 `passed` / `risk_level` / `issues` 三个字段
- 测端到端时合规必须通过才允许发布(`test_e2e.py` 用 `pytest.fail` 阻断),不要让 mock 草稿通过检查

## 环境变量一览

所有变量统一 `CF_` 前缀,缺省时对应能力降级到 mock。**永远不要**把真实 token 写进 frontmatter / 提交 / `.env`(放 `~/.zshrc` 或 `~/.bashrc`)。

| 变量 | 必需 | 用途 |
|---|---|---|
| `CF_TUSHARE_TOKEN` | 否 | Tushare `pro_api()` token |
| `CF_TUSHARE_BASE_URL` | 否 | myMCP 兼容端点(如 `https://tt.xiaodefa.cn/mcp/token=xxx`),启用则覆盖 Tushare 直连 |
| `CF_BIBIGPT_TOKEN` | 否 | BibiGPT 视频/音频摘要 token |
| `CF_MINIMAX_API_KEY` | 否 | MiniMax(妙想)多模态生成 |
| `CF_MINIMAX_GROUP_ID` | 否 | MiniMax Group ID |
| `CF_DATAPRO_TOKEN` | 否 | dataPro 专业检索 |
| `CF_BILIBILI_URL` | 否 | bilibili_toolkit 服务地址,默认 `http://127.0.0.1:8100` |
| `CF_BILIBILI_API_KEY` | 否 | B 站 API Key(可选) |
| `CF_TRENDRADAR_DB_DIR` | 否 | TrendRadar SQLite 目录,默认 `/Users/chenlei/001_project/TrendRadar/output/rss` |
| `CF_KNOWLEDGE_URL` | 否 | RAG 知识库地址,默认 `http://127.0.0.1:8002` |
| `CF_WECHAT_APPID` | 否 | 微信公众号 AppID |
| `CF_WECHAT_SECRET` | 否 | 微信公众号 Secret |
| `CF_DATABASE_URL` | 否 | PostgreSQL 连接串,启用 `PostgreSQLTenantManager` |
| `CF_TRACE_CONSOLE` | 否 | `1` 开启 OpenTelemetry ConsoleSpanExporter |

## 安全与隐私

- 本工程是**本地工具 + 文档仓库**,默认不暴露公网。生产部署参考 `docs/user-guide.md` 的「生产部署」章节,务必套反代 + 鉴权
- **不要**直接 `curl ... | bash` 跑未审计脚本(`scripts/*.sh`、`bin/*.sh` 全部先 `cat` 一遍)
- `.gitignore` 已屏蔽 `.env` / `*.local` / `drafts/` / `publish/` / `tracking/` / `logs/` / `serenity-skill/` / 早期 `0X-` 目录
- 公告 PDF 体积大,只 commit JSON 元数据,PDF 走 `drafts/raw/*/cninfo/pdfs/` 自动 ignore
- 详细安全策略见 `SECURITY.md`,支持版本:`1.0.x`(完整)/ `0.3.x`(仅严重安全更新)/ `<0.3` 不再支持
- 漏洞报告通过 GitHub Security Advisories 私下提交,48 小时内确认,30 天内修复(高危优先)

## 提交与变更

### Commit 格式

```
<scope>: <subject>

<body>
```

- scope 候选:`packages/<name>` / `SOP` / `scripts` / `docs` / `templates` / `data-source` / `compliance` / `工程化清理`
- subject ≤ 50 字,body 写「为什么 / 改了什么 / BEFORE → AFTER 数字对比」
- 例:`compliance-check.py: A17 软化 + A17b 新增 ZsxqCrawler 硬约束`

### Branch 命名

- `feat/<scope>-<short-desc>`(新功能)
- `fix/<scope>-<short-desc>`(修 bug)
- `docs/<scope>-<short-desc>`(文档)

### CI 检查

`.github/workflows/ci.yml` 跑 3 件事:

1. **lint** —— `ruff check` + `ruff format --check` + `mypy packages/adapters/cninfo/src/content_factory_cninfo`
2. **test** —— 矩阵 `Python 3.11 / 3.12 / 3.13 × ubuntu / macos / windows`,`ubuntu + 3.12` 上传 coverage 到 codecov
3. **build** —— `python -m build` + `twine check dist/*` + 上传 artifact(依赖前两步通过)

**任何 PR 在 FAIL 状态下禁止 merge**,详见 `CONTRIBUTING.md`。

## 新增功能的标准动作清单

写一个新数据源 / 编辑 / 发布器时,按顺序做:

1. 在 `docs/data-source-hierarchy.md`(数据源)或对应章节更新层级表
2. 在 `packages/<group>/<name>/` 新建子包,实现对应 Protocol
3. 写 entry point,在 `pyproject.toml` 的 `[project.entry-points."content_factory.<group>"]` 登记
4. `uv sync --all-packages`,确认 `discover_components()` 能识别
5. 在 `test_smoke.py` 加组件发现断言;必要时新建 `test_<name>.py`
6. 跑 `uv run pytest` 全绿
7. 更新 `README.md` 特性徽章与「环境变量」表
8. 在 `CHANGELOG.md` 的 `## [Unreleased]` 段加 `Added` 条目
9. PR 标题遵循 `<group>: <改动>`,描述写触发场景 / 改动详情 / 测试方式

## 关键文档索引

| 想了解 | 看哪里 |
|---|---|
| API 端点 + 租户管理 + A/B 测试示例 | `docs/user-guide.md` |
| 架构决策(为什么组件化 / 为什么 Temporal / 为什么 schema-level 隔离) | `docs/adr/001-component-based-architecture.md` |
| 数据源层级(主要/验证/理论支撑)与 11 个数据源职责 | `docs/data-source-hierarchy.md` |
| TrendRadar 15 类兴趣 ↔ 9 大主题映射 | `docs/ai-interests-mapping.md` |
| 公众号友好排版规则(emoji / 表格 / 链接损失) | `docs/cn-pub-style-guide.md` |
| 17 步 SOP + 工具栈优先级 | `SOP.md` |
| 数据单元规则 / 关系 / 去重 / 字段规范 | `SOURCE_OF_TRUTH.md`(新架构下作为存档) |
| 14 项合规清单唯一权威 | `templates/compliance/checklist.md` |
| v0.3 重构完成报告 | `REFACTORING_COMPLETE.md` |
| 鲁班工坊打磨报告(开源化分析) | `docs/luban-reports/content-factory-review-2026-07-05.md` |
| 整改项完成情况 | `TODO.md` |

## 常见陷阱

- **不要在 monorepo 之外的地方 import 适配器**:始终从 `registry.get_*()` 拿,否则组件替换会失效
- **Tushare 多 ts_code 一次调用易 502**:见 `content_factory_tushare` 实现,需逐家重试
- **微信公众号 access_token 缓存 7000 秒,提前 200 秒刷新**:见 `content_factory_wechat`,不要在每次发布时都拿新 token
- **OpenTelemetry 未安装时 `trace_span` 自动降级**:不要在业务代码里 try/except 包装它
- **合规检查不通过时阻断发布**:`test_e2e.py` 已示范,生产代码用 `compliance_result["passed"]` 判断
- **编辑组件的 `can_handle()` 简单按 tag 匹配**:扩展时考虑风险容忍度 + 行业偏好,而非只看 tag
- **Temporal workflow 中合规检查 Activity 不重试**:`RetryPolicy(maximum_attempts=1)`,失败需要人工介入
- **多租户 PostgreSQL 写入失败会自动降级内存**:不要假设数据一定落库,关键路径上加确认日志
- **不要在 `app.py` 之外发起 `discover_components()` 后修改组件**:entry point 只在导入时加载,运行时动态注册不被支持
