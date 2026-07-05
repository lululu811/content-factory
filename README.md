# content-factory

> **End-to-end pipeline for producing in-depth A-share investment articles for Chinese WeChat newsletters.**
>
> 投研型公众号深度文生产流水线 · 从选题、研究、写作、配图到合规发布的完整工程化方案

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Type checker: mypy](https://img.shields.io/badge/type%20checker-mypy-blue.svg)](https://mypy-lang.org/)
[![Tests: pytest](https://img.shields.io/badge/tests-pytest-green.svg)](https://pytest.org)

---

## 这是什么 / What is this?

`content-factory` 是一个**开源的工程化框架**,用来生产**A 股投研类公众号深度文**(每篇 8000-10000 字,带数据图表,带合规检查)。

它把生产流程拆成了 17 步 SOP,每一步都有对应的工具/脚本:

1. **选题**(topics-pool + topic-scorer)
2. **漏标防御扫描**(industry-kol-scan)
3. **数据采集**(myMCP / cninfo PDF 抓取)
4. **写作**(v2 模板 + 单股模板)
5. **配图**(matplotlib 信息图,深色科技风)
6. **合规检查**(16 项硬约束 + PASS/WARN/FAIL)
7. **发布** + **追踪**

`content-factory` 不是一个"AI 写作工具",而是一套**让 AI Agent 能可靠地生产合规深度文**的工程化基础设施。

## 核心理念 / Core Principles

- **数据精度第一** — 直接从 cninfo (巨潮) 和 myMCP (Tushare) 抓原始数据,不做二次总结
- **流程可执行** — 16 项 A1-A17b 合规检查,发布前自动门禁
- **工具简单** — 优先用 `requests` / `matplotlib` / `pdfplumber` 等标准库,不在反爬上钻牛角尖
- **可工程化** — 17 步 SOP 全部脚本化,AI Agent 友好
- **开源友好** — 所有流程/模板/SOP 都是公开方法论,不绑定特定主题

## 项目结构 / Project Structure

```
content-factory/
├── src/content_factory/             # 核心 Python 包(开源)
│   ├── cli.py                        # typer CLI: cf 主命令
│   ├── cninfo/                       # 巨潮公告抓取(anns + pdf-dl + pdf-extract)
│   ├── compliance/                   # 16 项合规检查
│   ├── images/                       # matplotlib 信息图
│   ├── research/                     # 行业情报扫描 + 三源数据校验
│   ├── pipeline/                     # 选题打分 + 17 步 SOP 编排
│   └── utils/                        # 共用工具
│
├── templates/                        # 文章模板
│   ├── post-template-v2.md           # v2 行业类模板
│   ├── post-template-single-stock.md # 单股深度模板
│   └── compliance/checklist.md       # 16 项合规清单(权威)
│
├── bin/                              # 一键发文脚本
│   ├── cf-new.sh                     # 行业类
│   └── cf-new-stock.sh               # 单股类
│
├── tests/                            # pytest 测试
│
├── docs/                             # MkDocs 文档
│   ├── installation.md
│   ├── quickstart.md
│   ├── sop.md                        # 17 步 SOP 文档
│   └── api.md
│
├── examples/                         # 端到端示例
│
├── scripts/                          # 已整合到 src/ 的脚本(保留兼容,下个大版本删除)
│
├── .github/workflows/ci.yml          # CI:lint + test 矩阵
│
├── SOP.md                            # 17 步 SOP(主文档)
├── topics-pool.md                    # 选题池
├── AGENTS.md / CLAUDE.md             # AI Agent 指引
├── README.md                         # 本文件
├── CHANGELOG.md / CONTRIBUTING.md / CODE_OF_CONDUCT.md / SECURITY.md / LICENSE
└── pyproject.toml                    # 项目元数据
```

## 安装 / Installation

```bash
pip install content-factory

# 或本地开发模式
git clone https://github.com/chenliitaz/content-factory.git
cd content-factory
pip install -e ".[dev]"
```

## 快速开始 / Quickstart

### CLI 方式

```bash
# 1. 查询公告
$ cf anns 600487.SH 300308.SZ --days 14 --json --output anns.json

# 2. 下载 PDF
$ cf pdf-dl --anns anns.json --output-dir ./pdfs/

# 3. 提取文本
$ cf pdf-extract --pdf-dir ./pdfs/ --output-dir ./extracted/

# 4. 一键跑全流程
$ cf pipeline 600487.SH 300308.SZ --days 14 --output-dir ./data/

# 5. 合规检查
$ cf compliance ai-fiber-value-chain

# 6. 生成配图
$ cf images bottleneck-matrix --slug ai-fiber-value-chain --data data.json
```

### Python API

```python
from pathlib import Path
from content_factory import (
    get_announcements,
    download_pdfs,
    extract_pdfs,
    ComplianceChecker,
    ImageGenerator,
)

# 公告查询 + 下载 + 解析
anns = get_announcements("600487.SH", days=14)
dl_report = download_pdfs(anns, output_dir=Path("./pdfs/"))
pdfs = [Path(r.local_path) for r in dl_report.results if r.success]
extract_pdfs(pdfs, output_dir=Path("./extracted/"))

# 合规检查
checker = ComplianceChecker(slug="ai-fiber-value-chain")
result = checker.run()
print(f"Passed: {result.passed_count}, Failed: {result.failed_count}")

# 配图生成
gen = ImageGenerator(slug="ai-fiber-value-chain")
gen.generate(chart_type="bottleneck-matrix")
```

## 17 步 SOP 概述

完整 SOP 见 [SOP.md](SOP.md)。这里列出 17 步:

| Step | 名称 | 工具/输出 |
|---|---|---|
| 1 | 选题拍板 | `topics-pool.md` 选主题 |
| 2 | 漏标防御扫描 | `cf research scan` → `00-kol-scan.md` |
| 3 | 行业情报扫描 | web_search → 32+ 权威源 |
| 4 | 数据采集 | `cf anns` + `myMCP` |
| 5 | 三源校验 | `cf research validate` |
| 6 | 写作(v2 模板) | `templates/post-template-v2.md` |
| 7 | 配图 | `cf images <type>` |
| 8 | 6 分类应用 | 前置勾选 |
| 9 | 5 分类应用 | 前置勾选 |
| 10 | 5 要素勾选 | 前置勾选 |
| 11 | 3 源对比表 | 写在附录 |
| 12 | 7+ 升级 / 6+ 降级 | tracking/predictions/ |
| 13 | 4+ 反共识 | 嵌入正文 |
| 14 | 必走检查 | `templates/compliance/checklist.md` |
| 15 | 配图调优 | Read 每张图 |
| 16 | 发布 | `cf compliance --strict` |
| 17 | 反馈响应 | 24-48h 反馈 → 附录 B |

## 16 项合规清单(发布前硬约束)

完整清单见 [`templates/compliance/checklist.md`](templates/compliance/checklist.md)。摘要:

- A1 标题含反共识钩子
- A2 候选公司 ≥ 18 家(行业类)
- A3 弱故事都有 Tickers
- A4 Top 7 含 5 要素
- A5 共识/分歧论证
- A6 配图 ≥ 5 张
- A7 数据时效(30 天内)
- A8 免责条款
- A9 强弱证据 🟢🟡🔴 齐
- A10 数据源 ≥ 10 个
- A11 高风险词 0 误用
- A12 时效窗口(H1 2026)
- A13 升降级信号
- A14 追踪记录
- A15 访谈引用
- A16 verified_sources + verified_at
- A17 research-reports / ZsxqCrawler 引用

## 模板 / Templates

- **`templates/post-template-v2.md`** — 行业类深度文模板(12 章 + 6 分类 + 4 反共识 + 附录)
- **`templates/post-template-single-stock.md`** — 单股深度模板(9 反共识 + 6 跟踪信号)
- **`templates/compliance/checklist.md`** — 16 项合规清单(权威)

## bin/ 一键脚本

```bash
# 行业类选题一键发文
$ bin/cf-new.sh ai-fiber-value-chain

# 单股类一键发文
$ bin/cf-new-stock.sh 603618.SH 石英股份
```

## 开发 / Development

```bash
# 设置 dev 环境
git clone https://github.com/chenliitaz/content-factory.git
cd content-factory
pip install -e ".[dev]"
pre-commit install

# 跑测试
pytest

# 跑 lint
ruff check src tests
ruff format src tests

# 跑 type check
mypy src/content_factory

# 构建 docs
mkdocs serve    # 本地预览
mkdocs build    # 静态构建
```

## 路线图 / Roadmap

- [x] 0.1.x — 单脚本阶段(2026-06 ~ 2026-07)
- [x] 0.2.x — 整合到 src/ 包 + typer CLI(2026-07)
- [ ] 0.3.x — 完整 pytest 覆盖 + CI 矩阵
- [ ] 0.4.x — MkDocs 文档站 + PyPI 发布
- [ ] 1.0.x — Stable API + 实战案例 10+

详见 [CHANGELOG.md](CHANGELOG.md)。

## 贡献 / Contributing

我们欢迎所有形式的贡献!详见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 许可证 / License

MIT License — 详见 [LICENSE](LICENSE)。

## 致谢 / Acknowledgements

- **myMCP (xiaodefa.cn)** — 免费的 Tushare 兼容 A 股数据
- **cninfo (巨潮资讯网)** — 公开的公告披露平台
- **所有早期试错的 11 篇已发布文章** — 没有它们就没这套 SOP

## 免责声明 / Disclaimer

`content-factory` 是一个**内容生产方法论 + 工具集**,不构成任何投资建议。

- 工具访问的是**公开数据**(cninfo 公告 / myMCP 行情)
- 生成的模板 / 清单 / SOP 都是**公开方法论**
- 已发布的文章 `publish/` 不在开源范围内(版权)
- 用户应**独立判断**所有投资决策

请遵守 cninfo 的[服务条款](http://www.cninfo.com.cn/new/disclosure)。