# ADR-001: 组件化平台架构

## 状态

已接受 (Accepted) - 2026-07-06

## 背景

`content-factory` 当前是一个本地 CLI 工具，用于生产投研型公众号深度文。项目痛点：

1. **单进程批处理**：CLI 驱动、串行执行、无断点续跑、无监控
2. **强耦合**：领域逻辑、外部依赖、配置全部混在一起
3. **难扩展**：新增数据源、编辑风格、发布渠道都需要改核心代码
4. **单人工具**：无法服务多租户、无法对外提供平台化服务

目标是将项目演进为：
- **高可用**的服务化平台（24×7 运行、可观测、可断点续跑）
- **低耦合**的领域模块化架构（领域间事件驱动、可独立部署）
- **组件化**的可扩展平台（第三方可发布组件、即插即用）
- **多租户**的平台化服务（对外提供编辑部 OS 能力）
- **多编辑风格**（AI 编辑 persona、风格可学习、可版本化）

## 决策

### D1: 采用组件化平台架构

项目重组为 **monorepo 多包结构**，分为 4 层：

```
Layer 4: Applications (server / cli)
Layer 3: Component Packages (领域组件 / 适配器组件 / 编辑组件)
Layer 2: Platform SDK (SPI 接口 / 事件总线 / 组件注册)
Layer 1: Core Runtime (领域模型 / 事件 schema / 配置管理)
```

每个组件是独立的 Python 包（`content-factory-xxx`），通过 Python entry points 机制注册，运行时自动发现。

**关键约束**：
- 组件间只能通过事件通信，禁止直接 import
- SDK 定义的 SPI 接口只能加不能改（语义化版本）
- 组件无状态，所有状态存 PostgreSQL（按 tenant 隔离）

### D2: 采用 Temporal 作为编排引擎

选择 Temporal 而非 Celery / Prefect / 自研 DAG，理由：
- 长 workflow（17 步 SOP，每步几分钟到几十分钟）
- 原生支持断点续跑、信号、人工审批节点
- 多租户隔离（Namespace + Isolation）
- Python SDK 成熟（1.x 系列）
- 可观测性内置（每个 workflow/activity 自动 trace）

代价：多跑一个 Temporal Server（Go 写的，吃 PostgreSQL）。

### D3: 采用事件驱动 + 领域模块化

项目按业务领域拆分，而非按技术层：

```
domains/{topic,research,writing,image,compliance,publish}/
platform/{temporal,events,persistence,observability,config,multi_tenancy}/
api/  workers/  cli/
```

**低耦合 3 个硬规则**：
1. 领域间只能通过事件通信，不能直接 import 别的领域的 models
2. 每个领域有自己的数据库 schema（逻辑隔离，共用 PostgreSQL 实例）
3. 外部依赖全部走 adapter，领域代码只依赖 adapter 接口

### D4: 采用 PostgreSQL 独立 schema 做多租户隔离

三种方案对比：
- 共享 schema + tenant_id 字段（逻辑隔离，复杂度低，隔离弱）
- **独立 schema（中等隔离，复杂度中，推荐起步）**
- 独立数据库（物理隔离，复杂度高）

选择独立 schema，理由：
- PostgreSQL 原生支持，迁移成本低
- 隔离够用（每个租户的表在不同 schema 下）
- 真到几百租户再考虑优化

### D5: 采用细粒度组件

组件粒度选择：
- 领域是组件（`content-factory-topic`）
- Adapter 也是组件（`content-factory-tushare`）
- 编辑风格也是组件（`content-factory-editor-yan-su`）

细粒度更灵活，换数据源不需要换整个 research 组件。

## 后果

### 正面
1. **可扩展**：第三方可写组件并发布，无需改核心代码
2. **低耦合**：领域可独立开发、测试、部署、替换
3. **高可用**：Temporal 保证断点续跑、失败重试、状态持久化
4. **多租户**：平台化服务的基础设施就位
5. **多编辑**：Editor 作为一等公民，风格可学习、可版本化
6. **可观测**：全链路 trace，任意时刻能回答"这篇文章卡在哪一步"

### 负面
1. **复杂度上升**：monorepo 多包管理、entry points 机制、事件总线
2. **学习曲线**：Temporal 概念多（workflow、activity、signal、query）
3. **部署复杂度**：需要跑 Temporal Server + PostgreSQL + Redis
4. **初期开发成本高**：搭骨架需要 2-3 周，之后才能快速迭代

### 风险
1. **Temporal 学习曲线**：团队需要 1-2 周熟悉，spike 阶段验证
2. **组件接口稳定性**：SPI 接口一旦发布只能加不能改，需要谨慎设计
3. **事件驱动调试**：跨组件问题排查比直接调用更难，需要良好的可观测性
4. **monorepo 工具链**：uv workspace 还不够成熟，可能需要 fallback 到 Poetry

### 缓解措施
1. 第 1 周做 spike，验证 Temporal 是否适合团队
2. SPI 接口先内部用 1-2 个月再发布 1.0，充分迭代
3. OpenTelemetry 全链路 trace，包括组件边界
4. 如果 uv workspace 有问题，可以切换到 Poetry workspace 或 PDM

## 迁移路径

### M1: 基础骨架（4-6 周）
- 第 1 周：monorepo 骨架 + SDK + mock 组件验证
- 第 2-3 周：迁移官方领域组件
- 第 4 周：Temporal server + server API + 多租户
- 第 5-6 周：可观测性 + CLI

### M2: 事件驱动 + 并行化（2-3 周）
- 引入 domain_events 表 + dispatcher
- 领域间解耦为事件通信
- 并行化（配图和合规可以同时跑）
- 合规审批节点（workflow 暂停等 signal）

### M3: 多编辑风格（3-4 周）
- Editor 领域 + 风格指纹学习
- 多编辑并行产出 workflow
- 风格一致性评估
- A/B 测试数据回流

### M4: 高级特性（按需）
- 组件市场
- Pipeline 版本化
- 多租户自助服务
- 人工介入 UI

## 参考

- [Temporal Python SDK](https://github.com/temporalio/sdk-python)
- [Python Entry Points](https://packaging.python.org/en/latest/specifications/entry-points/)
- [uv workspace](https://docs.astral.sh/uv/concepts/workspaces/)
- [Architecture Decision Record](https://adr.github.io/)
