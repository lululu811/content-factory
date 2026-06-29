# Changelog

content-factory 项目的所有重要变更记录。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/),
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

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
