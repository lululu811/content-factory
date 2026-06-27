# 内容工厂 SOP v2.0

> **本 SOP 是"公众号深度文生产流水线"的完整运作手册，基于 2 篇文章（AI 资源端 + 人形机器人）实际跑通经验沉淀。**
> **最后更新**：2026-06-20

---

## 一、整体定位

**做什么**：公众号深度文（生产 + 投研 + 趋势研判）
**目标**：每周 1-2 篇深度文，3-6 个月订阅 2000-5000，6-12 个月付费转化
**护城河**：结构化研究（Serenity 8 层级 + 5 分类 + 5 要素）+ 个人框架（zettaranc 极简版）

---

## 二、工具栈优先级

| 优先级 | 工具 | 角色 | 何时用 |
|---|---|---|---|
| 🥇 P0 | **Obsidian research-reports** | 内容中枢 | 所有选题都从这里开始 |
| 🥈 P1 | **ZsxqCrawler 飞书日报** | 市场观点对照 | 写作时查"市场在讨论什么" |
| 🥉 P2 | **bibigpt feed** | 音视频素材 | 选题灵感 / 单篇补研 |
| 🏅 P3 | **serenity-skill** | 深度补研 | 知识库没覆盖的新方向 |
| 🎨 工具 | **mmx image generate** | 视觉生产 | 封面 |
| 📊 工具 | **matplotlib** | 信息图 | **正文配图（比 mmx 强）** |
| 🧠 引擎 | **zettaranc-skill** | 表达引擎 | **极简版**，只用于个人判断 |
| ⚙️ 引擎 | **Serenity 方法论** | 表达引擎 | **核心**，占 70-80% 文章篇幅 |

---

## 三、周节奏

| 时间 | 动作 | 耗时 |
|---|---|---|
| 每天 8:00 | 自动：bibigpt feed + ZsxqCrawler pipeline | 0 |
| 周一晚 | 选题（合并 bibigpt 候选 + 飞书日报 + Obsidian 库） | 30 min |
| 周二下午 | 研究（serenity-skill + Obsidian 库检索 + web search） | 1 h |
| 周二/四晚 | **写作（v2 标准：20+ 公司、5 分类、5 要素）** | 2-3 h |
| 周二/四/六 | 发布（`publish.sh` 一键打包） | 30 min |
| 周五晚 | 知乎同步 + 即刻/小红书钩子 | 1 h |

**总投入**：~7-8 小时/周，**稳定产出 2 篇深度文**

---

## 四、内容生产 SOP（核心 v2 标准）

### 4.1 选题（第 1 步，30 min）

**自动化**：
```bash
# 每日 8:00 自动跑（cron）
bibi feed --limit 50 --json > drafts/candidates/feed-$(date +%Y-%m-%d).json

# 过滤：过去 7 天 + 时长 > 20 分钟
python3 scripts/filter-candidates.py
```

**手动（周一晚 30 min）**：
1. 打开 feed 候选清单
2. 跑 5 个问题过滤：
   - 6 个月后还有人搜这个话题吗？（搜索价值）
   - 30 秒内能说出 3 个原内容没覆盖的角度吗？（增量价值）
   - 能写出至少 1500 字有信息密度的内容吗？（产能匹配）
   - 写完这篇我会不会更懂这个领域？（个人成长）
   - 如果只有 50 个人看，我还会写吗？（动机检验）
3. **3 个 YES 才写**

**选题原则**：
- 不选已经"充分定价"的方向（GPU/光模块等热门赛道）
- 优先选**有卡点但市场讨论少**的方向
- 配合 Obsidian 库里的 MOC 主题（最大化素材复用）

### 4.2 研究（第 2 步，1 h）

**素材来源优先级**：

| 来源 | 用法 |
|---|---|
| **🆕 research-reports /query skill** | **Step 0 必跑**：在 `~/003_knowledge/knowledge_base/research-reports/` 的 1053 个概念 + 2181 个飞书日报里检索已有素材 |
| serenity-skill | 跑产业链深度研究（必跑） |
| web search (matrix_web_search) | 补 2026 H1 最新数据 |
| bibigpt summarize --chapter | 拿音视频素材结构化大纲 |

#### 4.2.1 research-reports /query 必跑（Step 0，硬约束）

**为什么放在第一位**：research-reports 已有 1053 个概念 + 2181 个飞书日报 source，是长期积累的高质量原料。**不查 = 浪费 = 文章浅**。

**强制 3 步**（写新文章前必跑）：

1. **快速扫**:跑 `bash scripts/research-reports-query.sh "<主题关键词>"` 看返回的 top 10 匹配概念
   - 例:`bash scripts/research-reports-query.sh "电力 算力 数据中心"`
   - 返回:`AI电力.md` / `AIDC.md` / `数据中心电源.md` / `核电.md` 等
2. **深度读**:对 top 5-10 概念,用 Read 工具读完整内容,提取关键数据/公司/观点
3. **写进 frontmatter**:在文章 frontmatter 加 `research_reports:` 字段,记录用过的概念 + 飞书日报源(详见 4.3.6)

**降级处理**:如果 research-reports 无相关内容,在 frontmatter 加 `research_reports.queried_at` + `research_reports.found_concepts: 0` 标记,而不是跳过不查。

**实测案例**(electric-power):
- 查询"电力 算力 数据中心" → 命中 10+ 概念:`AI电力.md`(142 行) / `核电.md` / `AI算力数据中心电力结构.md` 等
- 比单凭印象写深 3-5 倍

#### 4.2.2 serenity-skill + research-reports 互补

- **research-reports** = 你长期积累的"原料库"（已有数据 / 观点 / 关联）
- **serenity-skill** = 即时联网的"研究助手"（跑公告 / 财报 / 问询函）

两者互补:`/query` 先查 research-reports 已有 → 再跑 serenity-skill 补全最新 → 再 web_search 核验。

**serenity-skill 必跑 prompt 模板**：
```
用 serenity-skill 深度调研 {topic} 的产业链。
请联网查公告、财报、问询函、互动易、招投标、环评/能评、
专利、客户认证和财务质量，先排产业链层级，
再找 5 个最值得优先研究的标的，
并说明卡住的环节、产业链位置、证据、排序理由和主要风险。
输出 markdown 格式。
```

#### 4.2.3 🆕 Step 3 行业情报扫描（发文前必跑，防漏标防御）

**为什么这条**：2026/6/27 第 9 篇玻璃桥/CPO 写完 Top 7 后才发现 Step 3 industry-kol-scan.py 能扫出 6 家被漏标的真龙头（亨通/光迅/源杰/光库/剑桥/博创）。代价是 1 小时补丁 + 反共识 5 重构。**正确做法是发文前先跑，扫出的候选公司直接进 Top 7，不需要补丁**。

**强制流程**（A2 候选公司生成前必跑）：

```bash
# 0. 首次运行：拉取 myMCP stock_basic 全 A 股名单作为白名单(避免"新型光学封装"等误匹配)
python3 scripts/industry-kol-scan.py --setup-whitelist
# → 输出 ~/.cache/a-stock-names.json(5530 家公司)

# 1. 用 web_search 搜主题，收集 15+ 条结果
#    （mavis mcp call matrix web_search ... 或原生 web_search 工具）

# 2. 把结果喂给 industry-kol-scan.py
python3 scripts/industry-kol-scan.py \
  --topic "<主题>" \
  --slug <slug> \
  --input <web_search_results.json> \
  --include-non-a
# --include-non-a:同时读 scripts/non-a-stock-participants.md,把"非 A 股但关键"的公司一并标出
# 默认读 ~/.cache/a-stock-names.json 白名单,可加 --no-whitelist 禁用
# → 输出 drafts/raw/<slug>/00-kol-scan.md + 00-kol-scan.json

# 3. 人工核对 20+ 候选公司，检查是否覆盖 5 个产业链核心环节：
#    - 上游材料 / 设备
#    - 中游制造（光芯片 / 光器件 / 光模块 / 玻璃基板）
#    - 下游应用（数据中心 / AI 服务器 / 光通信）
#    - 海外大客户链（微软/Meta/亚马逊/英伟达）
#    - 跨界 / 蹭概念（对照组）
```

**漏标处理**：
- 扫描出但没在候选公司表的 → 补搜 → 加进 5 分类 → 再写 Top 7
- 扫描出但**确实是边缘公司**（市值/卡位/数据都不足） → 记录到 00-kol-scan.md 的"未列入"清单，写明原因

**反共识 N 补丁 vs 重排 Top 7**（发文后才发现漏标的决策）：
- **B 路径（反共识补丁，推荐）**：数据快照已锁，加"反共识 N:产业链完整性反思"节，列漏标的 N 家 + 三点反思。详见第 9 篇实战（commit d996ad7）。
- **A 路径（重排 Top 7）**：仅发文前发现漏标时使用。需要重跑 myMCP + cninfo + 重写 Top 7 + 重发。

**实战**：第 9 篇玻璃桥/CPO 漏标的 6 家：亨通光电（国内光纤双雄）/ 光迅科技（国内唯一 10G+ 光芯片）/ 源杰科技（国产光芯片龙头）/ 光库科技（CPO 光纤阵列）/ 剑桥科技（800G 微软/Meta/亚马逊）/ 博创科技（集成光电子）。

### 4.3 写作（第 3 步，2-3 h）—— **v2 标准（强制）**

**这是 v1 → v2 升级的核心**。v1 文章被批"产业链分析太浅"，v2 必须做到：

#### 4.3.1 文章模板（v2 标准）

| 节 | 内容 | 字数 | 占比 |
|---|---|---|---|
| 1 | 核心观点 + 证据等级说明 | 100-200 | 2% |
| 2 | 为什么现在写这个 | 200-300 | 3% |
| 3 | 主流叙事 vs 我的判断（3 条非共识） | 400-500 | 5% |
| 4 | Serenity 式 8 层级拆解（表格 + 壁垒评分） | 600-800 | 8% |
| 5-7 | **三大卡点深度分析**（每个含：市场结构 + 关键证据 + 海外/国内龙头对比） | 2,400-3,000 | 30% |
| 8 | **公司 5 分类**（Controls / Supplies / Benefits / Weak / Story，每节有具体公司名单 + 入选标准） | 1,000-1,200 | 12% |
| 9 | **优先研究 Top 7**（每个含 5 要素：环节 / 位置 / 原因 / 证据 / 风险） | 1,400-1,600 | 16% |
| 10 | **反共识判断**（3-4 类排名低的热门方向 + 为什么） | 400-500 | 5% |
| 11 | 个人判断（zettaranc 极简版，**只占 1 段**） | 150-200 | 2% |
| 12 | 风险 + 升降级信号 | 400-500 | 5% |
| 13 | Serenity 研究动作清单 | 200-300 | 3% |
| 14 | 一图收尾仪表盘 | - | - |
| 15 | 免责声明（中版本） | 100-150 | 2% |

**总字数**：8,000-10,000 字符（约 5,500-6,500 字正文）

#### 4.3.2 强制要求（v2 标准）

- ✅ **候选公司 ≥ 20 个**：Controls / Supplies / Benefits / Weak / Story 五大类都要有具体公司
- ✅ **Top 7 候选完整 5 要素**：每个都有"卡住的环节 / 产业链位置 / 排序原因 / 证据 / 主要风险"
- ✅ **反共识方向 ≥ 3 类**：必须包括"排名较低的热门方向"并解释为什么
- ✅ **数据时效**：所有数据用最近 6 个月内的（优先 2026 H1）
- ✅ **证据等级**：🟢🟡🔴 三档齐全，每条强结论都要标证据来源
- ✅ **数据源列表**：用最新版的报告（如 IEA《Energy and AI》2025，而不是 Electricity 2024）
- ✅ **数据时效校验（web_search 硬规则）**：所有公司的**股票代码 / 上市状态 / 财务数据 / 港股通状态**等动态字段，写入正文前**必须用 web_search 实时核验**，且在 frontmatter `data_verified` 字段记录核验时间 + 来源。**否则会被 A16 自动 FAIL**。

#### 4.3.2.1 数据时效校验硬规则（A16 必读）

**为什么要这条**：2026/6/24 E 篇被打脸 —— 把"摩尔线程"写成"待上市"（实际 2025/12/5 已上市 688795.SH），沐曦股份代码写错 688710→真实 688802，壁仞科技代码写错 0606.HK→真实 06082.HK。**记忆/印象里的财务数据可能已经过期几个月甚至一年**。

**强制 4 步**：

1. **候选公司表写入前**：每家公司用 `web_search "<公司名> 2026 财务 上市状态"` 实时查一次。**禁止用记忆/印象**。
2. **frontmatter 必填**：
   ```yaml
   data_verified:
     verified_at: "2026-06-24"          # 最后一次核验日期
     verified_sources:                  # 至少 1 个来源
       - "https://www.qcc.com/firm/..."
       - "https://www.bing.com/search?q=..."
     verified_companies:                # 核验过的公司清单
       - "摩尔线程 (688795.SH)"
       - "沐曦股份 (688802.SH)"
       - "壁仞科技 (06082.HK)"
   ```
3. **候选公司表的每个数字旁**：加 `[✅ verified 2026-06-24]` 标记（合规检查 A16 会扫描）
4. **publish 前强制**：跑 `compliance-check.py --strict`，A16 FAIL 直接拒绝发布

**核验频率建议**：上市公司状态变化很快（IPO / 退市 / 港股通 / ST），**写文章时核验一次够，但发布前 24 小时内**最好再扫一眼。

#### 4.3.3 zettaranc 占比压到 10% 以下

之前 v1 文章用了 35 处 zettaranc 关键词（"三最原则 / B1/B2/B3 / 底仓/动态仓 / 防守哲学"），太多。

**v2 标准**：zettaranc 关键词 ≤ 3 处，**只在第 11 节"个人判断"里简短提一下**（如"会等回踩确认再加配置"），不展开。

#### 4.3.4 配图策略（v2 改进）

| 类型 | 工具 | 用途 |
|---|---|---|
| **封面** | mmx image generate（投研 prompt） | 文章首图 |
| **信息图** | **matplotlib + Python** | 8 层级、卡点矩阵、价格走势、收尾仪表盘 |
| ~~章节图~~ | ~~mmx image generate~~ | ❌ v1 用过，太 low。**改用 matplotlib** |

**关键经验**：投研类公众号的图，**优先用 matplotlib 数据图** 而不是 AI 抽象生图 —— 数据图自带"信息密度"和"专业感"。

#### 4.3.5 合规（强制）

每篇发布前过 `templates/compliance/checklist.md` 10 项检查。
高风险词（"买入/卖出/目标价/推荐/保证/加仓/稳赚"等）只能出现在免责声明反向表达中。

#### 4.3.6 🆕 research-reports 查证记录（frontmatter 硬约束）

**为什么这条**：把 research-reports 跟 content-factory 双向打通的关键——**让每篇文章都自带 research-reports 的深度**,同时反向登记"这篇文章用了 research-reports 哪些原料"。

**frontmatter 必填字段**：

```yaml
research_reports:
  queried_at: "2026-06-25"           # research-reports /query 调用时间
  found_concepts: 12                 # 命中的概念数
  read_concepts: 8                   # 实际深度读的概念数
  linked_concepts:                   # 用到的概念（指向 research-reports 里的文件）
    - name: "AI电力"
      path: "wiki/concepts/AI电力.md"
      used_for: "电力板块定位 + 4 大赛道画像"
    - name: "核电"
      path: "wiki/concepts/核电.md"
      used_for: "中国核电 vs 中国广核双寡头对比"
  linked_sources:                    # 用到的飞书日报 source
    - date: "2025-06-16"
      path: "wiki/sources/摘要-2025-06-18-核聚变+核电+铀矿更新.md"
      used_for: "核电保底机制最新数据"
  skipped_reason: ""                 # 如果 found_concepts = 0,说明跳过原因
```

**正文中的引用**：在文章正文引用 research-reports 概念时,用 Obsidian 双链 `[[概念名]]` 格式(让 Obsidian 用户能直接跳转)。

**自动化检查**(后续可加):compliance-check.py 加 A17 检查——`research_reports.queried_at` 距今 ≤ 30 天。

### 4.4 配图生成（matplotlib 标准）

每个主题至少 5 张图：

| # | 图 | 类型 |
|---|---|---|
| 1 | 8 层级壁垒排序 | 横向条形图 |
| 2 | 卡点矩阵（扩产难度 × 估值预期） | 散点图 + 象限 |
| 3 | 价格走势（关键品类） | 折线图 |
| 4 | 关键趋势（需求 / 供给 / 替代规模） | 柱状图或折线图 |
| 5 | 收尾总结仪表盘 | 复杂 dashboard（多个 subplot） |

**风格统一**：深色背景（`#0f1419`）+ 高对比度色彩（黄/橙/红/绿/蓝）+ 去除 emoji 字符（字体不一定支持）+ 中文字体用 `PingFang SC / Hiragino Sans GB`。

### 4.5 发布

**自动化脚本**：`scripts/publish.sh <slug>` 一键打包。

```bash
# 用法
./scripts/publish.sh morgan-ai-supply-chain

# 输出
~/content-factory/publish/final/morgan-ai-supply-chain/
├── morgan-ai-supply-chain.md
├── 发布说明.md
└── images/（6 张图）
```

**发布前自动跑合规检查**（v3 · 14 项）：

```bash
# 单篇
python3 scripts/compliance-check.py <slug>
# 加 --strict:任意 FAIL 直接 exit 1(适合 publish.sh 集成)

# 全部草稿
python3 scripts/compliance-check.py --all
```

**建议集成到 publish.sh**：在 cp 到 final 之前跑 `compliance-check.py --strict`,有 FAIL 直接 `exit 1`。这样发布流程自带合规门禁,人工不会忘。

---

## 五、合规清单（强制）

> **清单的唯一权威来源**：`templates/compliance/checklist.md`(v3 · 14 项,2026-06-21 合并 SOP 与原合规清单)。
> 每篇发布前必过。**不在 SOP 中维护清单副本**——避免两边走偏。

**简版速查**(完整版 + 加重场景 + 一句话口诀见模板文件):

- **A. 内容硬约束**(7 项):标题 ≤ 30 字 / 公司 ≥ 20 / 9.4·9.5 必须给代码 / Top 7 5 要素 / 反共识 ≥ 3 / 配图 ≥ 5 / 数据 2026 H1
- **B. 合规与证据**(7 项):免责声明 / 证据等级 / 来源可查 / 高风险词 0 / 时间窗口 / 升降级信号 / tracking 自动写入

**发布前自动化检查**(推荐):
```bash
python3 scripts/compliance-check.py <slug>   # 自动化勾选 + PASS/FAIL
```

---

## 六、可复用资产清单

```
~/content-factory/
├── SOP.md                           # 本文件
├── templates/
│   ├── compliance/                  # 合规模板（11 个）
│   │   ├── account-bio.md
│   │   ├── disclaimer-*.md
│   │   ├── evidence-level.md
│   │   ├── wording-table.md
│   │   ├── checklist.md
│   │   ├── multi-platform.md
│   │   ├── special-scenarios.md
│   │   ├── paid-product.md
│   │   └── red-line-card.md
│   └── post-template-v2.md          # v2 文章模板
├── scripts/
│   ├── daily-feed.sh                # bibigpt 选题
│   ├── filter-candidates.py         # feed 过滤
│   ├── image-gen.py                 # matplotlib 信息图
│   ├── serenity-research.sh         # serenity 跑研究
│   └── publish.sh                   # 一键打包发布
└── docs/
    ├── prompt-pack.md               # Serenity prompt 模板
    └── tools.md                     # 工具栈详细说明
```

---

## 七、v1 → v2 升级经验沉淀

| v1 问题 | v2 修复 |
|---|---|
| Serenity 只做了 8 层级拆解，没列具体公司 | **强制 20+ 候选公司**，按 5 分类 |
| 公司只点名没分析 | **Top 7 完整 5 要素**（环节/位置/原因/证据/风险） |
| 缺反共识判断 | **强制 3 类排名低的热门方向 + 解释为什么** |
| zettaranc 占 35 处 | **压到 ≤ 3 处**，只用于个人判断 |
| 数据陈旧（IEA Electricity 2024） | **用最新版**（IEA《Energy and AI》2025） |
| 图用 mmx 生抽象图 | **改用 matplotlib 数据图**（信息密度高 10 倍） |
| mermaid 代码块不能公众号渲染 | **改用 matplotlib PNG** |
| emoji 字符字体缺失 | **改用字母+符号**（◆ ● ▲ ▼） |
| 数据源未标注具体日期 | **每条数据标日期**（如"Mysteel 2026/6/12"） |

---

## 八、cron 自动化（必备）

**安装命令**：`crontab -e`,粘贴以下两行:

```cron
# 每天 8:00 抓 bibigpt feed + 过滤(写入 drafts/candidates/feed-YYYY-MM-DD.json)
0 8 * * * /Users/chenlei/content-factory/scripts/daily-feed.sh

# 每季度首月 1 号 9:00 跑 verify-predictions + compliance-check + 生成季度报告
0 9 1 */3 * /Users/chenlei/content-factory/scripts/quarterly-review.sh
```

**季度报告输出位置**:
- 战绩表:`~/content-factory/tracking/reports/战绩表-{YYYY-Q#}-{YYYYMMDD}.md`
- 季度日志:`~/content-factory/tracking/reports/quarterly-review-{YYYYMMDD}.log`

**飞书 webhook 推送(可选)**:在 `quarterly-review.sh` 第 85 行附近取消注释,填入 `FEISHU_WEBHOOK_URL`。

---

## 九、未来扩展（M7+ 启用）

- 付费产品合规（`templates/compliance/paid-product.md`）
- 知乎/即刻/小红书同步 SOP
- B 站视频版本 SOP
- 行业月报 / 季报 SOP
- 投研工具订阅（M7+）

---

**维护者**：Mavis / 内容工厂主理人
**更新频率**：每跑 5 篇文章回看一次，更新经验沉淀