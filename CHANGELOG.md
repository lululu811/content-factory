# Changelog

content-factory 项目的所有重要变更记录。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/),
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

---

## [Unreleased]

### Added
- `.env.example` — 14 个 `CF_*` 环境变量样例(任何缺失自动降级 mock)
- `SECURITY.md` — 支持版本矩阵 + 漏洞报告通道(GitHub Security Advisories)
- `.pre-commit-config.yaml` — ruff check / format + 关键 yaml / smoke test 钩子
- `.github/ISSUE_TEMPLATE/{bug_report,feature_request,question}.md`
- `.github/PULL_REQUEST_TEMPLATE.md` — 类型 / 测试 / 文档自检清单
- `docs/compliance/checklist.md` — 从 `templates/compliance/` 迁出,合规清单唯一权威可见
- `examples/quickstart_e2e.py` — 30 秒端到端示例

### Changed
- **`pyproject.toml` root version**: `0.3.0` → `1.0.0`(与 CHANGELOG 对齐)
- 全部 23 个子包 `version` 与 `__version__` 同步到 `1.0.0`
- `pyproject.toml`: ruff `target-version` `py39` → `py311`,`src` 改为 `packages`,`mypy.files` 改为 `packages`
- `pyproject.toml`: pytest `testpaths=["tests"]` → `["."]`,因根目录集成测试无 `tests/` 父目录;`--cov=content_factory` → 各 `--cov=content_factory_*` 精确覆盖
- `.github/workflows/ci.yml`:`ruff check src tests` → `ruff check packages test_*.py`
- `.github/workflows/ci.yml`:`mypy src/content_factory/cninfo` → `mypy packages/adapters/cninfo/src/content_factory_cninfo`
- `.github/workflows/ci.yml`:Python 矩阵 `3.9 / 3.10 / 3.11 / 3.12 / 3.13` → `3.11 / 3.12 / 3.13`(与 requires-python 对齐)
- `.github/workflows/ci.yml`:`pip install -e ".[dev]"` 全部改为 `uv sync --all-packages --dev`,安装 pip/uv 与 uv step
- `packages/server/content_factory_server/app.py`:`FastAPI(version="0.3.0")` 与 `HealthResponse(version="0.3.0")` 改为动态 `__version__`
- `README.md`:badge `tests-9_passed` / `components-12_registered` 改为 `ci-passing` 动态徽章
- `README.md`:补全「文档」索引(数据源层级 / 公众号样式指南 / AI interests 映射 / 鲁班报告 / SECURITY / examples)
- `README.md`:CF_TUSHARE_BASE_URL 默认示例改为占位符
- `CONTRIBUTING.md`:`python3 scripts/compliance-check.py` → `uv run pytest` / `uv run ruff check` / `uv run cf components`
- `CONTRIBUTING.md`:`加新数据源` 章节补 4 步标准化流程 + pyproject.toml 模板 + SPI 接口指路
- `bin/cf-new*.sh` 与 `bin/cninfo-pipeline.sh`:`CF_ROOT` 默认 `~/content-factory`(原来写死 `/Users/chenlei/content-factory`)
- `scripts/publish.sh` 与 `scripts/daily-feed.sh`:`WORKDIR` 同上
- `docs/data-source-hierarchy.md`、`docs/cn-pub-style-guide.md`:顶部加 status 段说明 `scripts/*.py` 已 gitignore,新用户改用 packages/*/ 模块式入口
- `SOURCE_OF_TRUTH.md`:顶部加 ⚠️ deprecated 状态,指向 AGENTS.md

### Fixed
- CI lint job 之前因为 `src/ tests/` 路径找不到代码而必失败,现已对齐到 packages/
- CI test job 之前因为 `testpaths=["tests"]` 而 collect 0 用例,现已能 collect 9 个测试
- `e2e` 测试的合规阻断是按设计主动 `pytest.fail()`,不是 bug

### P2 增量 (2026-07-09)
- **CI uv cache**:`.github/workflows/ci.yml` 三处 `astral-sh/setup-uv` 加 `enable-cache: true` + `cache-dependency-glob: "uv.lock"`,build 时间从 ~3min 降到 ~1min
- **`fail_under = 40`**:pyproject `[tool.coverage.report]` 强制覆盖率门槛(当前 51.9% 留出空间给新代码),PR 提交覆盖率下降会拒绝合并
- **`examples/` 5 个端到端脚本**:quickstart_e2e、ab_test_run、compliance_strict_demo、multi_tenant_demo、data_source_fallback;`examples/README.md` 含命令索引
- **lint/mypy 全清零**:`ruff check` 0 error、`ruff format --check` 41/41 通过、`mypy packages/adapters/cninfo` (strict) 0 issue
- 33 个 ruff 历史 lint 错误分类修复:
  - 16 E402 测试文件 shebang 位置修正(`#!/usr/bin/env python3` 提至顶)
  - 5 B904 CLI `raise typer.Exit(1) from e`
  - 1 B904 `raise HTTPException from exc`(FastAPI 边界)
  - 1 B904 `raise RuntimeError from exc`(psycopg import fallback)
  - 5 unused import 清理(topic / writing 包的 `Any` / `uuid4` / `Editor` / `UUID`)
  - 2 unused variable(`compliance_strict_demo.found` 与 temporal `research_id`)
  - 1 B905 `zip(strict=False)`
  - 1 UP042 `class CheckStatus(StrEnum)`(替代 `class CheckStatus(str, Enum)`)
  - 11 个 E402 / 3 个 E402 / 24 个 import-sort 等由 `ruff check --fix` 自动修

### P2 第 1 项:OTel OTLP + Prometheus 接入 (2026-07-09)

#### Added
- **`prometheus-client` 接入**:`packages/server/content_factory_server/observability.py` 的 `Metrics` 类双后端实现
  - 安装 `prometheus-client` 时:走 `Counter` / `Gauge` / `Histogram` 全局 registry,`/metrics` 输出 exposition format `text/plain; version=0.0.4`,可被 Prometheus / VictoriaMetrics 直接抓取
  - 未安装时:走内存字典 + JSON snapshot(向后兼容)
- **OTel OTLP HTTP exporter**:`init_tracing` 检测 `CF_TRACE_OTLP=1` 时启用
  - endpoint 默认 `http://localhost:4318/v1/traces`,可用 `CF_TRACE_OTLP_ENDPOINT` 覆盖
  - 未装 `opentelemetry-exporter-otlp` 时降级到日志告警,不影响主流程
- **`packages/server/pyproject.toml` `[project.optional-dependencies]` 段**:增 `observability` extra
  - `uv sync --all-packages --extra observability` 一键装 OTLP + Prometheus
  - 默认依赖保持最小,避免强制 OTel collector 依赖
- **`render_metrics_prometheus` / `metrics_content_type` 函数**:方便 `app.py` 的 `/metrics` 路由根据后端自适应返回

#### Changed
- `observability.py` 重写为双后端,但公共 API 完全兼容(increment / gauge / observe / snapshot)
- `app.py` 的 `/metrics` 路由根据 `PROMETHEUS_AVAILABLE` 自适应返回格式

---

## [1.0.0] - 2026-06-29

### 🎉 首次开源

**从个人工作流转为可工程化、可复用的开源项目。**

### Added
- **LICENSE**:MIT(完全开源)
- **README.md**:项目导览(17 步 SOP + 3 类数据源 + 工具栈优先级 + 路线图)
- **.github/workflows/ci.yml**:GitHub Actions 自动跑 compliance-check
- **.gitignore**:完整规则(本地保留 10 篇已发布文章 + dbs 7 目录 + tracking)
- **SOP.md "二、工具栈优先级" 重构**:TrendRadar P0 / ZsxqCrawler P1 / myMCP P2
- **A17b ZsxqCrawler 原始导出硬约束**:compliance-check.py 新增
- **templates/post-template-v2.md 加 zsxq_crawler 字段**:下次发文自然合规

### Changed
- **SOP 4.2 研究阶段重构**:ZsxqCrawler 升 P0(必跑 Step 0)
- **A17 research-reports 软化**:从硬约束改为软提示(WARN if 缺)
- **daily-feed cron 暂停**:bibi 账户额度耗尽,TrendRadar 50 feed 完全覆盖
- **tracked 文件数 446 → 289**(-157 个本地保留)

### Removed
- drafts/candidates / outlines / research / raw/demo / raw/lip-bu-tan-no-priors
- logs/ / reports/ 临时文件
- dbs-content-system 7 目录(00-07 早期试错)
- 9 篇已发布深度文(drafts/posts/*.md,版权)
- 14 个 archives 归档(本地保留)

---

## [0.3.0] - 2026-06-28

### Added
- **SOP 4.1.1 TrendRadar AI interests 接入**:15 类兴趣 × 9 大主题映射
- **SOP 4.2.1 ZsxqCrawler 原始导出 Step 0 必跑**:扫文件 + 章节 grep + 段落读
- **SOP 4.3.6 A17 软化 + 4.3.7 A17b 新增**:A17b ZsxqCrawler 硬约束
- **docs/data-source-hierarchy.md**:3 类数据源层级(主要/验证/理论)
- **docs/trendradar-feeds-debug.md**:TrendRadar 排查报告
- **scripts/industry-kol-scan.py**:Step 3 行业情报扫描(防漏标)
- **scripts/cninfo-anns.py**:巨潮公告查询
- **scripts/cn-pub-beautify.py**:公众号自动美化

### Changed
- **TrendRadar 真实订阅刷新**:5 公众号 → 50 feed(微信公众号 10 + B 站 22 + 财经新闻英文 18)
- **数据源认知更新**:从 5 个公众号 → 50 feed 实际订阅

---

## [0.2.0] - 2026-06-25

### Added
- **dbs-content-system**:7 个标准目录(00-07 内容资产工程)——**后续废弃**
- **SOP.md v2.0**:公众号深度文生产流水线
- **content-factory 9 篇深度文**:
  - morgan-ai-supply-chain
  - asean-ai-supply-chain
  - ai-three-bottlenecks
  - cicc-ai-population
  - electric-power
  - liquid-cooling
  - glass-substrate
  - glass-bridge-cpo
- **templates/post-template-v2.md**:v2 文章模板
- **templates/compliance/**:11 个合规模板
- **scripts/compliance-check.py**:A1-A14 + A16 自动检查
- **scripts/image-gen.py**:matplotlib 信息图

### Workflow
- 17 步 SOP 4.1-4.5(选题 → 研究 → 写作 → 配图 → 发布)
- v2 强制要求:20+ 公司 / 5 分类 / Top 7 / 反共识 ≥ 3

---

## [0.1.0] - 2026-06-20

### Added
- 初始 SOP.md
- 第一个深度文骨架(morgan-ai-supply-chain)

---

## 版本说明

### 1.0.0 = 开源里程碑
- 第一个适合外部用户的稳定版本
- LICENSE / README / CI 完整
- 所有临时/隐私内容已隔离

### 0.3.0 = 流程定型
- ZsxqCrawler + TrendRadar + cninfo 三大数据源形成闭环
- 17 步 SOP 跑通 9 篇实战

### 0.2.0 = 起步
- dbs-content-system 7 目录(后期废弃)
- 9 篇深度文 v2 模板实战

### 0.1.0 = 雏形
- SOP v1
- 第一篇实战
