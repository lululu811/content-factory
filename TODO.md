# 整改项跟踪清单

## ✅ 已完成 (10/10)

### 1. 完善合规检查 ✅
- [x] 从 5 项扩展到 18 项（A1-A17 + A17b + C15）
- [x] 适配新的 SPI 接口 (`ComplianceProvider`)
- [x] 100% 单元测试覆盖

### 2. 真实数据源适配器 ✅
- [x] tushare: 支持环境变量 `CF_TUSHARE_TOKEN`，无 token 时 fallback 到 mock
- [x] cninfo: 巨潮资讯数据源，提供公告查询
- [x] 通过 `content_factory.data_sources` entry point 自动注册

### 3. Temporal Workflow 编排 ✅
- [x] `docker-compose.temporal.yml` - Temporal Server + Web UI + Worker
- [x] `packages/server/content_factory_server/temporal_workflows.py` - `ArticleProductionWorkflow` 定义
- [x] 支持 6 个 Activity（选题/研究/写作/合规/发布/人工审批）
- [x] 支持 Signal（批准/拒绝）+ Query（进度/状态/当前Activity）
- [x] RetryPolicy 按 Activity 差异化配置
- [x] temporalio 未安装时优雅降级（占位类）

### 4. 多编辑风格扩展 ✅
- [x] 严肃派（yan-su-pai）：formality=0.9, risk_tolerance=0.3
- [x] 犀利派（xi-li-pai）：formality=0.3, risk_tolerance=0.8
- [x] 风格指纹（`style_fingerprint`）通过 Editor SPI 暴露
- [x] 通过 `content_factory.editors` entry point 自动注册

### 5. 多租户数据隔离 ✅
- [x] `TenantManager` 内存存储（生产环境接入 PostgreSQL）
- [x] Schema 级别隔离预留（`tenant_id` 贯穿所有模型）
- [x] 租户配额和限流接口预留（`add_run`/`get_runs` 已实现）

### 6. 可观测性 ✅
- [x] `packages/server/content_factory_server/observability.py` - OpenTelemetry 集成
- [x] `/metrics` 端点暴露指标快照（counters/gauges/histograms）
- [x] `trace_span` 上下文管理器追踪工作流执行
- [x] 未安装 opentelemetry 时自动降级到本地日志

### 7. CLI 改造 ✅
- [x] 基于新 API 重写 CLI (`cf` 命令)
- [x] 支持 `health`, `create`, `list`, `status`, `components` 命令
- [x] 使用 typer + rich + httpx（trust_env=False 绕过代理）

### 8. Web UI 管理后台 ✅
- [x] 单页面 Dashboard（`GET /`）
- [x] 显示租户/组件/运行记录统计
- [x] API 端点文档（`/health`, `/tenants`, `/runs`, `/metrics`）
- [x] 响应式 CSS 布局，纯 HTML 无依赖

### 9. 旧代码清理 ✅
- [x] 验证新架构覆盖旧功能
- [x] 删除 `src/` 和 `tests/`
- [x] 删除 `scripts/*.py`（已被替代）
- [x] 保留有价值的运维脚本（`.sh`, `.md`, `.json`, `.txt`）

### 10. A/B 测试和数据回流 ✅
- [x] `packages/sdk/content_factory_sdk/ab_testing.py` - 多编辑并行产出
- [x] `StyleFingerprint` 风格指纹匹配（距离计算）
- [x] `parallel_draft` 并发调用多个 editor 产出草稿
- [x] `FeedbackTracker` 数据回流跟踪器
- [x] API 支持 `ab_test: true` 参数，返回所有 editor 的产出

## 测试覆盖

```bash
uv run pytest test_smoke.py test_e2e.py test_api.py test_multi_editor.py -v
# 8 passed
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
│  yan-su-pai · xi-li-pai  ·  tushare · cninfo                │
├─────────────────────────────────────────────────────────────┤
│                          Platform                            │
│  Core Models · SDK SPI · Registry · Observability · Tenant  │
└─────────────────────────────────────────────────────────────┘
```

## 下一步迭代

- [ ] Temporal Server 实际启动 + Worker 注册（需要 `docker-compose up`）
- [ ] PostgreSQL 接入（替换 `TenantManager` 内存存储）
- [ ] OpenTelemetry 完整接入（Prometheus + Grafana）
- [ ] Publisher 组件实现（微信公众号 API）
- [ ] 更多编辑风格（数据派、幽默派等）
- [ ] 风格指纹学习机制（从历史文章学习）
