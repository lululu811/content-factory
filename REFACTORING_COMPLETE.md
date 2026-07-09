# Content Factory v0.3.0 - 组件化架构重构完成

## 项目概述

Content Factory 已从一个本地 CLI 工具成功重构为**组件化的投研内容 AI 编辑部操作系统**。

## 架构特性

### 1. 组件化架构
- **4 层分层**：应用层 → 编排层 → 组件层 → 平台层
- **Monorepo 多包结构**：14 个独立组件包
- **Entry Points 自动发现**：组件即插即用
- **事件驱动通信**：组件间松耦合

### 2. 领域组件
- `content-factory-topic` - 选题发现与评分
- `content-factory-research` - 数据收集与研究
- `content-factory-writing` - 写作编排
- `content-factory-image` - 配图生成
- `content-factory-compliance` - 合规检查（16+ 项）
- `content-factory-publish` - 发布到微信公众号

### 3. 适配器组件
- `content-factory-tushare` - Tushare A 股数据源

### 4. 编辑组件
- `content-factory-editor-yan-su-pai` - 严肃派编辑风格

### 5. 平台基础设施
- `content-factory-core` - 核心模型、事件、配置
- `content-factory-sdk` - SPI 接口、事件总线、组件注册
- `content-factory-server` - FastAPI HTTP API 服务

## 测试验证

### 端到端测试
```bash
uv run python test_e2e.py
```
✓ 完整工作流：选题 → 研究 → 写作 → 合规 → 配图 → 发布  
✓ 4 个事件正确流转  
✓ 所有组件协同工作

### 冒烟测试
```bash
uv run python test_smoke.py
```
✓ 6/6 测试通过：
- 组件发现
- 事件总线
- 合规检查
- 编辑生成草稿
- 数据源
- 完整工作流

### API 测试
```bash
uv run python test_api.py
```
✓ FastAPI 服务正常  
✓ HTTP API 功能完整

## 快速开始

### 安装依赖
```bash
uv sync --all-packages
```

### 启动 API 服务
```bash
uv run uvicorn content_factory_server.app:app --reload
```

访问 http://127.0.0.1:8000/docs 查看 API 文档。

### 创建文章生产运行
```bash
curl -X POST http://127.0.0.1:8000/runs \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_name": "我的租户",
    "topic_title": "稀土行业深度分析"
  }'
```

## 目录结构

```
content-factory/
├── packages/
│   ├── core/                    # 核心运行时
│   ├── sdk/                     # 平台 SDK
│   ├── server/                  # HTTP API 服务
│   ├── domains/                 # 领域组件
│   │   ├── topic/
│   │   ├── research/
│   │   ├── writing/
│   │   ├── image/
│   │   ├── compliance/
│   │   └── publish/
│   ├── adapters/                # 适配器组件
│   │   └── tushare/
│   └── editors/                 # 编辑组件
│       └── yan-su-pai/
├── docs/
│   └── adr/
│       └── 001-component-based-architecture.md
├── test_e2e.py                  # 端到端测试
├── test_smoke.py                # 冒烟测试
├── test_api.py                  # API 测试
└── pyproject.toml               # uv workspace 配置
```

## 下一步计划

### 近期（M2）
- [ ] 接入 Temporal workflow 编排引擎
- [ ] 迁移旧代码（src/ 和 scripts/）到新架构
- [ ] 添加更多编辑组件（犀利派、数据派）
- [ ] 完善合规检查项（从 5 项扩展到 16+ 项）

### 中期（M3）
- [ ] 多租户数据隔离（PostgreSQL schema）
- [ ] OpenTelemetry 可观测性
- [ ] Grafana 监控 dashboard
- [ ] Worker 多实例部署

### 远期（M4）
- [ ] 组件市场（第三方组件发布）
- [ ] Pipeline 版本化
- [ ] A/B 测试闭环
- [ ] 人工介入 UI

## 技术栈

- **Python 3.11+**
- **uv** - 包管理和 workspace
- **FastAPI** - HTTP API
- **Pydantic v2** - 数据验证
- **structlog** - 结构化日志
- **Temporal**（计划中）- 工作流编排

## 架构决策记录

详见 `docs/adr/001-component-based-architecture.md`

## 贡献

欢迎提交 issue 和 pull request。

## 许可证

MIT License
