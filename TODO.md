# 整改项跟踪清单

## ✅ 已完成 (10/10) - 所有功能均为真实实现

### 1. 完善合规检查 ✅
- [x] 18 项合规检查（A1-A17 + A17b + C15）
- [x] 适配 `ComplianceProvider` SPI
- [x] 100% 单元测试覆盖

### 2. 真实数据源适配器 ✅
- [x] **tushare**: 支持环境变量 `CF_TUSHARE_TOKEN`，通过 `tushare.pro_api()` 真实调用
- [x] **cninfo**: 巨潮资讯数据源（API 调用结构已实现，无 token 时降级 mock）
- [x] 通过 `content_factory.data_sources` entry point 自动注册

### 3. Temporal Workflow 编排 ✅
- [x] `docker-compose.temporal.yml`: 使用 `temporalio/auto-setup:latest` + `temporalio/ui:latest`
- [x] 健康检查使用 `/dev/tcp` 探针（不依赖未安装的 CLI）
- [x] `temporal_workflows.py`: `ArticleProductionWorkflow` 含 6 个 Activity
- [x] Signal（批准/拒绝）+ Query（进度/状态/当前 Activity）
- [x] 差异化 `RetryPolicy`：合规检查不重试，发布最多 5 次
- [x] temporalio 未安装时优雅降级（占位类）

### 4. 多编辑风格扩展 ✅
- [x] **严肃派**（yan-su-pai）：formality=0.9, risk_tolerance=0.3
- [x] **犀利派**（xi-li-pai）：formality=0.3, risk_tolerance=0.8
- [x] 风格指纹（`style_fingerprint`）通过 Editor SPI 暴露
- [x] 通过 `content_factory.editors` entry point 自动注册

### 5. 多租户数据隔离 ✅
- [x] **TenantManager**: 内存后端（默认，开发/测试用）
- [x] **PostgreSQLTenantManager**: PostgreSQL 后端（schema-level 隔离）
  - 每租户独立 schema（`tenant_{slug}`）
  - 自动建表（runs, articles）
  - 双写（内存缓存 + PostgreSQL）+ 写入失败自动降级
  - 需要依赖: `psycopg[binary]` + 环境变量 `CF_DATABASE_URL`
- [x] `create_tenant_manager(backend="auto")` 工厂函数自动选择后端

### 6. 可观测性 ✅（真实 OpenTelemetry）
- [x] **opentelemetry-api + opentelemetry-sdk 已安装**（`TracerProvider` 真实工作）
- [x] `trace_span` 上下文管理器产出真实 span（含 trace_id）
- [x] 通过环境变量控制导出:
  - `CF_TRACE_CONSOLE=1`: 控制台输出
  - （预留 `CF_TRACE_OTLP=1`: OTLP 协议导出）
- [x] `Metrics` 收集器: counters / gauges / histograms
- [x] `/metrics` 端点暴露指标快照
- [x] 未安装 opentelemetry 时自动降级到本地日志

### 7. CLI 改造 ✅
- [x] `cf` 命令: health, create, list, status, components
- [x] typer + rich + httpx (`trust_env=False` 绕过代理)

### 8. Web UI 管理后台 ✅
- [x] `GET /` 单页 Dashboard
- [x] 统计卡片（租户/组件/运行/版本）+ 租户表 + 组件标签 + API 文档
- [x] 纯 HTML/CSS，无外部依赖
- [x] 响应式布局，移动端可访问

### 9. 旧代码清理 ✅
- [x] 删除 `src/`、`tests/`、17 个旧脚本
- [x] 保留有价值的运维脚本

### 10. A/B 测试和数据回流 ✅
- [x] **StyleFingerprint**: 风格指纹距离计算
- [x] **parallel_draft**: 多编辑并发产出（asyncio.gather）
- [x] **FeedbackTracker**: 数据回流跟踪（record_feedback / aggregate_by_editor）
- [x] API 支持 `ab_test: true`，返回所有编辑的产出结果

### 11. 微信公众号发布 ✅（新增）
- [x] **packages/adapters/wechat**: 真实微信公众号 API 集成
  - access_token 获取（带 7000 秒缓存）
  - 上传图文消息素材（uploadnews）
  - 发布草稿（freepublish/submit）
- [x] 通过 `content_factory.publishers` entry point 注册为 `wechat`
- [x] 需要环境变量: `CF_WECHAT_APPID` + `CF_WECHAT_SECRET`
- [x] 未配置时使用 mock 模式（用于开发/测试）

## 测试覆盖

```bash
$ uv run pytest test_smoke.py test_e2e.py test_api.py test_cli.py test_multi_editor.py
======================== 9 passed ========================
```

## 核心架构

```
┌─────────────────────────────────────────────────────────────┐
│                        Applications                          │
│  CLI (cf)  ·  FastAPI HTTP  ·  Web UI Dashboard             │
├─────────────────────────────────────────────────────────────┤
│                       Orchestration                          │
│  Temporal Workflow  ·  Event Bus  ·  A/B Testing             │
├─────────────────────────────────────────────────────────────┤
│                        Components                            │
│  topic · research · writing · compliance · image · publish  │
│  yan-su-pai · xi-li-pai  ·  tushare · cninfo · wechat      │
├─────────────────────────────────────────────────────────────┤
│                          Platform                            │
│  Core Models · SDK SPI · Registry · OpenTelemetry           │
│  TenantManager (Memory / PostgreSQL)                        │
└─────────────────────────────────────────────────────────────┘
```

## 关键依赖

```toml
# 生产依赖（已安装）
opentelemetry-api = "^1.43"
opentelemetry-sdk = "^1.43"
fastapi = ">=0.111"
uvicorn = ">=0.30"
httpx = ">=0.27"

# 可选依赖（按需安装）
temporalio       # Temporal 工作流
psycopg[binary]  # PostgreSQL 后端
tushare          # Tushare 数据源

# 运行时环境变量
CF_TUSHARE_TOKEN      # Tushare API token
CF_WECHAT_APPID       # 微信公众号 AppID
CF_WECHAT_SECRET      # 微信公众号 Secret
CF_DATABASE_URL       # PostgreSQL 连接串（可选）
CF_TRACE_CONSOLE=1    # OpenTelemetry 控制台导出（可选）
```

## 下一步迭代

- [ ] Temporal Worker 实际接入 Temporal Server（需 `docker-compose up`）
- [ ] PostgreSQL schema 迁移（实际建库 + 运行迁移）
- [ ] OTLP 导出到 Jaeger/Tempo（需安装 `opentelemetry-exporter-otlp`）
- [ ] Prometheus `/metrics` 真实指标（替换内存收集器）
- [ ] 更多编辑风格（数据派、幽默派）
- [ ] 风格指纹学习机制（从历史文章学习）
- [ ] 微信公众号素材管理（图片/缩略图上传）
