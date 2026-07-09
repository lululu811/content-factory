# Contributing to content-factory

感谢你考虑为 **content-factory** 做出贡献!这是一套投研型公众号深度文生产流水线,基于 9 篇实战经验沉淀。

## 🎯 项目目标

让任何投研型公众号主理人(或个人投资者)都能:
- **数据精度第一** —— 从 ZsxqCrawler 原始 .md 直接读,不依赖二次总结
- **流程可执行** —— 17 步 SOP + 18 项 A1-C15 合规检查
- **工具简单** —— 优先用 rg/jq/curl,不钻 SPA 反爬
- **可工程化** —— AI Agent 友好

## 🤝 如何贡献

### 报告 Bug

发现 SOP 错误 / 脚本 bug / 文档问题:
1. 先看 [issues](https://github.com/lululu811/content-factory/issues) 是否有重复
2. 用 [.github/ISSUE_TEMPLATE/bug_report.md](.github/ISSUE_TEMPLATE/bug_report.md) 模板新建
3. 提供:触发条件、期望结果、实际结果、错误日志、`uv run python -c "import content_factory_core; print(content_factory_core.__version__)"` 输出

### 提改进建议

有更好的 SOP 流程 / 新工具想法 / 数据源接入:
1. 用 [.github/ISSUE_TEMPLATE/feature_request.md](.github/ISSUE_TEMPLATE/feature_request.md) 模板
2. 描述:痛点、建议方案、影响范围(改哪些包)

### 提交代码

#### 改 SOP / 文档

1. 改 `SOP.md` / `docs/` 下任一文件
2. PR 标题:`docs/SOP: <改动>` 或 `SOP X.Y: <改动>`
3. 跑 `uv run pytest test_smoke.py` 确保冒烟通过

#### 改 Python 代码

1. 在 `packages/<group>/<name>/` 下改对应包的 `__init__.py` 与 `*.py`
2. 新增组件必须按 § "加新数据源 / 编辑 / 发布器" 实现 SPI 接口
3. PR 标题:`packages/<name>: <改动>` 或 `compliance: <改动>`
4. 提交前:`uv run ruff check packages test_*.py && uv run ruff format --check packages test_*.py && uv run pytest test_smoke.py`

#### 加新数据源 / 编辑 / 发布器(标准流程)

对应 `packages/<group>/<name>/` 任一子包。按以下 4 步完成:

1. **写包骨架**

   ```bash
   mkdir -p packages/adapters/<name>/content_factory_<name>
   ```

   `packages/adapters/<name>/pyproject.toml`:

   ```toml
   [project]
   name = "content-factory-<name>"
   version = "1.0.0"
   requires-python = ">=3.11"
   dependencies = [
       "content-factory-sdk",
       # 适配器需要的外部依赖
   ]

   [tool.uv.sources]
   content-factory-sdk = { workspace = true }

   [project.entry-points."content_factory.data_sources"]
   <name> = "content_factory_<name>:<Name>DataSource"

   [build-system]
   requires = ["hatchling"]
   build-backend = "hatchling.build"

   [tool.hatch.build.targets.wheel]
   packages = ["content_factory_<name>"]
   ```

2. **实现 SPI 接口**(`content_factory_<name>/__init__.py`):

   适配器实现 `content_factory_sdk.spi.DataSourceProvider`;编辑器实现 `EditorProvider`;合规器实现 `ComplianceProvider`;发布器实现 `PublisherProvider`。Protocol 在 `packages/sdk/content_factory_sdk/spi.py`。

3. **加到 workspace 索引**:根 `pyproject.toml` 的 `[tool.uv.workspace]` members 已含 `packages/adapters/*`,无需手动加。

4. **同步 + 验证**:

   ```bash
   uv sync --all-packages --dev    # 让 entry point 重新生效
   uv run cf components            # 应该看到新组件出现在对应类别
   uv run pytest test_smoke.py     # 组件发现断言通过
   ```

5. **文档同步**:
   - `docs/data-source-hierarchy.md` 加一行
   - `README.md` 特性表加一行
   - `CHANGELOG.md ## [Unreleased]` 加 Added 条目
   - PR 标题:`data-source: 加 <name>` 或 `<group>: 加 <x>`

## 📝 提交规范

### Commit 格式

```
<scope>: <subject>

<body>
```

- **scope**: `SOP` / `scripts` / `docs` / `templates` / `data-source` / `compliance` / `packages/<name>` / `工程化清理`
- **subject**: ≤ 50 字
- **body**: 为什么 / 改了什么 / BEFORE → AFTER 数字对比

**好例子**:
```
compliance: A17 软化 + A17b 新增 ZsxqCrawler 硬约束
```

**坏例子**:
```
fix bug
```

### Branch 命名

- `feat/<scope>-<short-desc>`(新功能)
- `fix/<scope>-<short-desc>`(修 bug)
- `docs/<scope>-<short-desc>`(文档)

## 🛠 开发环境

### 前置

- Python 3.11+
- [uv](https://github.com/astral-sh/uv)(workspace 同步必备)
- ripgrep(`brew install ripgrep`)
- 可选:`mavis MCP` + `playwright MCP`(用于测试 TrendRadar 集成)

### 本地测试

```bash
# 全量测试
uv run pytest

# 单测 + 覆盖率
uv run pytest --cov=content_factory_server --cov-report=term-missing

# Lint / Format
uv run ruff check packages test_*.py
uv run ruff format --check packages test_*.py

# 验证 .gitignore 规则
git check-ignore -v <path>

# 验证 tracked 文件数
git ls-files | wc -l
```

### Pre-commit

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

## 🚫 不接受的贡献

- ❌ 主动抓取(SPA 反爬)—— 优先用订阅/RSS/web_search
- ❌ 物理删除内容 —— 工程化清理用 .gitignore 模式(本地保留)
- ❌ broad .gitignore pattern(伤及无辜)
- ❌ 跳过 CI 的 PR(任何 lint / test FAIL 拒绝 merge)
- ❌ 提交真实 `CF_*` token

## 📜 License

贡献的代码采用 [MIT License](./LICENSE) 发布。
贡献的内容(包括 SOP / 文档 / 工具)同样适用。

## 🙏 致谢

感谢所有早期试错者(包括 dbs-content-system 7 目录)—— 失败是开源的燃料。
