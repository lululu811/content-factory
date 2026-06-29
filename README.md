# content-factory

> **公众号深度文生产流水线 · 投研型公众号方法论工程化**
>
> 从选题、研究、写作、配图到合规发布的完整 SOP，配合一套自动化工具脚本。

---

## 这是什么

`content-factory` 是为**投研型公众号主理人**设计的内容生产流水线,基于 9 篇深度文（每篇 8000-10000 字符）的实战经验沉淀。

核心理念：
- **数据精度第一** —— 从 ZsxqCrawler 原始 .md 直接读，不依赖二次总结的知识库
- **流程可执行** —— 16 项 A1-A17b 合规检查 + 17 步 SOP，文章发布前自动门禁
- **工具简单** —— 优先用 rg/jq/curl 这类命令行工具，不在反爬/主动抓取上钻牛角尖
- **可工程化** —— 所有流程可脚本化，AI Agent 友好

---

## 快速开始

### 读者（想用这套方法）

```bash
# 1. 读主 SOP
cat SOP.md

# 2. 看数据源 + 决策树
cat docs/data-source-hierarchy.md

# 3. 套文章模板
cp templates/post-template-v2.md drafts/posts/my-new-article.md
```

### 贡献者（想改 SOP 或脚本）

```bash
# 1. 看项目入口
cat AGENTS.md
cat CLAUDE.md

# 2. 看源头规则
cat SOURCE_OF_TRUTH.md

# 3. 改任何 .md/.py/.sh 后跑合规检查
python3 scripts/compliance-check.py --all
```

---

## 目录导览

### 🟢 核心工程（GitHub 上能看到）

```
content-factory/
├── SOP.md                              # 主编排:4.1-4.5 选题→研究→写作→配图→发布
├── AGENTS.md / CLAUDE.md / README.md   # AI Agent / Claude Code 项目入口
├── SOURCE_OF_TRUTH.md                  # 项目唯一权威规则
├── LICENSE                             # MIT
├── .gitignore                          # 已 ignore 个人内容 + 临时文件
│
├── docs/                               # 方法论文档
│   ├── data-source-hierarchy.md        # 3 类数据源层级(主要/验证/理论)
│   ├── cn-pub-style-guide.md           # 公众号 10 条样式规则
│   ├── ai-interests-mapping.md         # TrendRadar AI interests 映射
│   └── trendradar-feeds-debug.md       # TrendRadar 排查报告
│
├── templates/                          # 文章 + 合规模板
│   ├── post-template-v2.md             # v2 深度文模板(含 A16/A17b frontmatter)
│   ├── post-template-interview.md      # 访谈版模板
│   ├── tldr-template.md                # TL;DR 摘要卡片
│   ├── section-hooks-template.md       # 章节钩子
│   ├── moc-routing.md                  # MOC 路由规则
│   ├── query-templates.md              # 检索 query 模板
│   └── compliance/                     # 11 个合规模板
│       ├── checklist.md                # 唯一权威合规清单(v3 · 18 项)
│       ├── disclaimer-*.md             # 3 个免责声明版本
│       ├── evidence-level.md           # 🟢🟡🔴 证据等级
│       └── ...
│
├── scripts/                            # 自动化工具
│   ├── compliance-check.py             # A1-A17b 自动检查(publish --strict)
│   ├── cninfo-anns.py                  # 巨潮公告查询
│   ├── industry-kol-scan.py            # 行业情报扫描(防漏标)
│   ├── cn-pub-beautify.py              # 公众号自动美化
│   ├── bibi-safe.py                    # 音视频 fetch(防 hallucination)
│   ├── topic-scorer.py                 # 选题评分
│   ├── tracking-record.py              # 预测追踪
│   ├── verify-predictions.py           # 季度预测验证
│   ├── image-gen.py                    # matplotlib 信息图
│   ├── paused-channels.txt             # 暂停订阅名单
│   ├── rss-channels.json               # RSS 频道配置
│   ├── non-a-stock-participants.md     # 非 A 股产业链参与者清单
│   └── ...
│
├── bin/                                # 命令入口
│   └── cf-new.sh                       # 一键发文(6 步封装)
│
├── publish/                            # 发布产物
│   ├── final/                          # 各文章发布包(MD + 图 + 说明)
│   └── images/                         # 封面图(各文章子目录)
│
└── serenity-skill/                     # 第三方依赖(Serenity 8 层级方法论)
```

### 🟡 本地保留(已 .gitignore,不上传)

- `drafts/posts/*.md` — 已发布 9 篇深度文(版权)
- `archives/2026-06/*.md` — 已发布归档
- `02-内容单元库/` `03-处理状态/` `04-模板/` `05-主题地图/` `06-选题装配/` `07-脚本与工具/`
  — 早期试错的 dbs-content-system 7 目录(已废弃)
- `tracking/predictions/` `tracking/reports/` — 个人战绩/预测
- `logs/` `reports/` `drafts/candidates/` `drafts/outlines/` `drafts/raw/demo/`
  — 运行日志 + 临时文件

---

## 核心流程（17 步 SOP 4.1-4.5）

```
[每日 8:00 cron]
  TrendRadar (44 feed, 1139 条/日)
  + myMCP cninfo + ZsxqCrawler 自动同步
        ↓
[周一晚 30 min]  4.1 选题
  • 跑 5 问过滤 → 选 1 个开干
        ↓
[周二下午 2-3h]  4.2 研究
  • Step 0: 扫 ZsxqCrawler 原始 + 章节 grep(精度最高)
  • Step 1: serenity-skill 产业链深度
  • Step 1.5: industry-kol-scan 防漏标
  • Step 2-4: web_search + cninfo + myMCP
        ↓
[周二/四晚 2-3h]  4.3 写作
  • v2 模板:20+ 公司 / 5 分类 / Top 7 / 反共识 ≥ 3
  • matplotlib 配图 ≥ 5 张
  • frontmatter: A16 data_verified + A17b zsxq_crawler 硬约束
        ↓
[周二/四/六 30 min]  4.5 发布
  • compliance-check.py --strict(16 项自动检查)
  • publish.sh 一键打包
  • 公众号粘贴 + 知乎/即刻同步
```

---

## 数据源（3 类层级）

| 类别 | 数量 | 用途 | 出现位置 |
|---|---|---|---|
| 🟢 主要数据源 | 7 | 写文章主要依据 | 正文数据 + Step 0/3 |
| 🟡 验证数据源 | 3 | 交叉验证/披露 | A16 data_verified |
| 🔵 理论支撑 | 3 | 背景/方法论 | 概念框架 + MOC |

详细见 `docs/data-source-hierarchy.md`。

---

## 合规清单（16 项 + 18 子项）

详见 `templates/compliance/checklist.md` —— 唯一权威。
`scripts/compliance-check.py` 自动化实现,`publish.sh` 集成 `--strict` 模式。

**最新更新(2026/6/28)**:
- A17 research-reports 软化(WARN if 缺)
- A17b ZsxqCrawler 原始导出硬约束(FAIL if 缺)
  - `zsxq_crawler.queried_at` ≤ 30 天
  - `cited_sections` ≥ 1
  - `citations` ≥ 1 项(除非 skipped_reason)

---

## 工具栈优先级

```
🥇 TrendRadar  (50 feed, AI 智能筛选, 1139 条/日)
🥈 ZsxqCrawler (2895 条原始, 精度最高)
🥉 myMCP       (Tushare 兼容 258 工具)
4️⃣  cninfo + industry-kol-scan + web_search + serenity
5️⃣  research-reports(降级,只作概念索引)
```

---

## 路线图

### M1 (v2 标准,已发布 9 篇)
- ✅ A1-A14 + A16 数据时效 + A17b ZsxqCrawler
- ✅ cninfo 公告 + industry-kol-scan 防漏标
- ✅ matplotlib 配图 + 公众号 10 条样式

### M2 (进行中)
- ⏳ 知乎/即刻/小红书同步 SOP
- ⏳ 投研工具订阅(JPMorgan/Goldman/MS 邮件 → TrendRadar)
- ⏳ 季度战绩自动生成(verify-predictions.py + reports)

### M3 (未来)
- ⬜ B 站视频版本 SOP
- ⬜ 行业月报/季报 SOP
- ⬜ 付费产品合规(已写模板 templates/compliance/paid-product.md)

---

## 贡献指南

- **改 SOP**:先看 SOURCE_OF_TRUTH.md,任何变动需要更新 changelog
- **改脚本**:跑 `python3 scripts/compliance-check.py --all` 确保通过
- **加新数据源**:更新 docs/data-source-hierarchy.md + SOP.md
- **加新 frontmatter 字段**:同步更新 templates/compliance/checklist.md + compliance-check.py

---

## License

MIT © 2026 content-factory contributors
