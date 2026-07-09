# 内容工厂 SOP v2.0

> **本 SOP 是"公众号深度文生产流水线"的完整运作手册，基于 2 篇文章（AI 资源端 + 人形机器人）实际跑通经验沉淀。**
> **最后更新**：2026-06-20
>
> ⚠️ 本 SOP 多次提及 `scripts/compliance-check.py`、`scripts/cn-pub-beautify.py` 等路径。这些脚本已被 `.gitignore` 标记本地保留(monorepo v0.3 起,新工具迁至 `packages/<group>/<name>/content_factory_<name>/`)。
> 等价入口:
> - 合规清单:`docs/compliance/checklist.md`(原 `templates/compliance/checklist.md`)
> - 新数据源接入:见 [CONTRIBUTING.md](./CONTRIBUTING.md) § 加新数据源

---

## 一、整体定位

**做什么**：公众号深度文（生产 + 投研 + 趋势研判）
**目标**：每周 1-2 篇深度文，3-6 个月订阅 2000-5000，6-12 个月付费转化
**护城河**：结构化研究（Serenity 8 层级 + 5 分类 + 5 要素）+ 个人框架（zettaranc 极简版）

---

## 二、工具栈优先级(2026/6/29 重构)

> **关键变化**:Obsidian research-reports 降级为概念索引(精度低于 ZsxqCrawler 原始);
> TrendRadar 升 P0(50 feed, 1302 条/日,完全覆盖 bibi/RSS)。

| 优先级 | 工具 | 角色 | 何时用 |
|---|---|---|---|
| 🥇 P0 | **TrendRadar** | 选题雷达 | 每日 8:00 跑 50 feed → AI 筛选 → Top 50-80 候选 |
| 🥈 P1 | **ZsxqCrawler 原始导出** | 精度最高源 | 研究阶段 Step 0:扫文件 + 章节 grep + 段落读(必跑) |
| 🥉 P2 | **myMCP (Tushare 兼容)** | 硬数据 | 估值/股价/市值/资金流(每日 1302+ 数据点) |
| 4️⃣ 工具 | **cninfo + industry-kol-scan + web_search** | 公告 + 防漏标 | 研究阶段补全 + A16 核验 |
| 5️⃣ 降级 | **Obsidian research-reports** | 概念索引 | 仅作 MOC 主题关联,不作为数据源(详见 4.3.6) |
| 🎨 工具 | **matplotlib** | 信息图 | 正文配图(mmx 已退休) |
| ⚙️ 引擎 | **Serenity 方法论** | 表达引擎 | **核心**,占 70-80% 文章篇幅 |
| 🧠 引擎 | **zettaranc-skill** | 表达引擎 | **极简版**,只用于个人判断(≤ 3 处) |

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

### 4.1.1 选题兴趣配置（基于 TrendRadar AI interests · 2026/6/28 真实订阅刷新）

**为什么这条**：TrendRadar 是用户的自建热点雷达项目（v6.10.0 + MCP v4.1.0），**实际订阅 44 个 feed**（不是早期认知的"5 个公众号 + 20 平台"），分 4 大类：
- **微信公众号 4 个**（每个 10 条/日）：华尔街见闻 / 半导体产业纵横 / TMT 研究院 / 产业投研院
- **B 站 UP 主 22 个**（每个 30-40 条/日）：小Lin说 / 半佛仙人 / 笨笨韭菜 / BOSS墨 / 创新药魔力 / 付鹏 / 黑鸦 / 红杉汇 / 华夏基金 / 雷神 / 厉害财经 / 卢克文 / 莫大韭菜 / 史诗级韭菜 / 王自如 / 雪球官方 / 战国时代 / 知行合一 / 追寻Alpha / 张小珺商业访谈录 / Web3天空之城 / 小白投资笔记
- **财经/新闻/英文 18 个**：财联社电报+头条 / 华尔街见闻实时 / 36氪快讯+最新 / 界面 / 中国日报财经 / 财新 / 雪球精华 / 21世纪经济报道 / 新财富 / 棱镜 / 雅虎财经 / Hacker News / 虎嗅 / Solidot / cnBeta
- **半导体产业链专用 AI 兴趣**（`custom/ai/semiconductor.txt`）：10 类优先级 + 过滤规则，专攻半导体/AI算力/光通信/先进封装

**每日产出**：`output/rss/YYYY-MM-DD.db` 1139 条 → AI 智能筛选 → Top 50-80 候选。

**数据流**：
```
TrendRadar (44 feed × 4 类)
   ├─ wewe-rss(微信公众号 4):每个 10 条/日
   ├─ RSSHub(财经快讯 9 + B 站 UP 主 22)
   └─ Hacker News / Yahoo Finance / Solidot / cnBeta(英文科技 4)
   ↓ daily 抓取(8:00 cron)+ AI 智能筛选(ai_interests.txt 15 类 + custom/ai/semiconductor.txt 半导体专用)
   ↓ output/rss/YYYY-MM-DD.db (sqlite, ~1139 条/日)
   ↓ Top 50-80 高质量候选(过滤标题党/营销/无信息源)
content-factory
   ↓ 4.1 选题：看 TrendRadar 今日 AI 筛选结果
   ↓ 4.1.1 兴趣映射：跟 9 大主题做对照
   ↓ 4.2 研究：扫 ZsxqCrawler 原始 + 抓具体公司 + 公告
```

> **重要更新（2026/6/28）**：早期 SOP 误以为 TrendRadar 只有 5 个微信公众号，实际 44 个 feed 每日 1139 条（含 B 站 UP 主 22 个 + 半导体专用 AI 兴趣）。**刷新 SOP 时务必看 TrendRadar 最新 config.yaml，不要凭印象**。

**15 类兴趣 × 9 大主题 映射表**（已发 9 篇 + 选题库）：

| # | TrendRadar 兴趣类 | content-factory 已覆盖 | 空白 / 待补 |
|---|---|---|---|
| 1 | 中国科技与互联网公司（DeepSeek/华为/腾讯/字节） | 第 6 篇 ai-three-bottlenecks（陈立武 Intel CEO） + 第 1-2 篇 | 京东战略 / 字节产品节奏 |
| 2 | 大模型与 AI 产品（OpenAI/Claude/Qwen/DeepSeek） | 部分覆盖 | **Qwen / GLM / DeepSeek-Coder 详细对比** ← 选题 5 |
| 3 | AI 基础设施与云算力（英伟达/AMD/CUDA） | 第 6 篇 + 第 7-9 篇 + 选题 1/2 | **Token 算租** ← 选题 2 |
| 4 | 芯片与半导体制造（光刻机/先进封装） | **第 7 篇 liquid-cooling + 第 8 篇 glass-substrate + 第 9 篇 glass-bridge-cpo（3 篇强项）** | HBM / ASIC / 算力金属 |
| 5 | 智能汽车与自动驾驶（比亚迪/FSD/智驾） | 部分覆盖（摩根士丹利闭门会） | 比亚迪出海 / FSD 中国落地 |
| 6 | 机器人与具身智能（宇树/智元/大疆） | 第 4 篇 cicc-ai-population | **灵巧手 2.0** ← 选题 4 |
| 7 | 全球科技巨头（苹果/微软/谷歌/OpenAI） | 部分覆盖 | OpenAI vs Claude 财报对决 |
| 8 | 地缘政治与国际关系（关税/制裁/脱钩） | 部分覆盖（第 8 篇台积电） | 中美 AI 芯片管制升级 |
| 9 | 金融市场与宏观政策（美联储/汇率） | 部分覆盖（第 7 篇电力） | 美元降息对 A 股科技股影响 |
| 10 | 能源与电力系统（光伏/水电/核电） | **第 5 篇 electric-power** | 雅鲁藏布江项目 / 核电重启 |
| 11 | 航天与深空探索（SpaceX/卫星） | 未覆盖 | **商业航天** ← 选题 3 |
| 12 | 前沿科学技术（量子/脑机接口） | 未覆盖 | 量子计算商用化 |
| 13 | 文化 IP 与内容产业（黑神话/三体） | 未覆盖 | 不写(消费品赛道跨度过大) |
| 14 | 零售与消费品牌（胖东来） | 未覆盖 | 不写(同上) |
| 15 | 国家与区域观察（背景） | 间接覆盖 | — |

**实际选题 vs 已发对照**：

| 选题 | TrendRadar 触发源 | content-factory 已发 | 状态 |
|---|---|---|---|
| 选题 1 AI Memory Crunch | 财新 / Bloomberg / 半导体产业纵横 "HBM" + "美光长协 220 亿" | 第 3 篇 ai-three-bottlenecks 部分提 | 🆕 待开干 |
| 选题 2 Token 算租 | 产业投研院 "算力租赁+独家壁垒" | 未覆盖 | 🆕 待开干 |
| 选题 3 商业航天 | TrendRadar AI interests #11 + 6/25 飞书日报 | 未覆盖 | 🆕 待开干 |
| 选题 4 灵巧手 2.0 | TrendRadar AI interests #6 + 6/25 飞书日报 | 第 4 篇 cicc-ai-population | 🆕 接续 |
| 选题 5 China Coding | All-In Pod 6/27 + Bloomberg 6/27 | 未覆盖 | 🆕 待开干 |

**TrendRadar AI 筛选结果接入流程**（每日 9:00 跑）：
```bash
# 1. 看 TrendRadar 今日 AI 筛选结果
python3 << 'EOF'
import sqlite3
c = sqlite3.connect('~/001_project/TrendRadar/output/rss/2026-06-28.db')
c.row_factory = sqlite3.Row
for r in c.execute('''
    SELECT i.title, i.url, f.name, f.id
    FROM rss_items i
    JOIN rss_feeds f ON i.feed_id = f.id
    WHERE i.id IN (SELECT item_id FROM ai_filter_analyzed_news WHERE score > 0.7)
    ORDER BY i.id DESC LIMIT 20
'''):
    print(f'[{r["name"]}] {r["title"][:80]}')
    print(f'  {r["url"]}')
EOF

# 2. 跟 content-factory 9 大主题做对照(4.1.1 映射表)
# 3. 选 3 个候选 → 跑 5 问过滤(4.1)
# 4. 选 1 个开干
```

**44 个 feed × 4 类分组**（TrendRadar 真实订阅清单，2026/6/28 刷新）：

| 类别 | 数量 | 代表 feed | 每日文章 | 看点 |
|---|---|---|---|---|
| 🟢 **微信公众号** | 4 | wechat-wsj / wechat-bdt / wechat-tmt / wechat-cytouyan | 各 10 条 = 40 条 | 深度报告 + 行业分析 |
| 🟢 **B 站 UP 主** | 22 | xiaolinshuo / banfoxianren / 笨笨韭菜 / 卢克文工作室 / 付鹏 / 雷神 / 王自如 / 张小珺商业访谈录 等 | 各 30-40 条 ≈ 680 条 | 音视频深度 + 大众解读 |
| 🟢 **财经/新闻/英文** | 18 | 财联社/华尔街见闻/36 氪/财新/21财经/新财富/Hacker News/Yahoo Finance/Solidot/cnBeta | 各 5-75 条 ≈ 415 条 | 实时快讯 + 深度报道 |
| 🟢 **半导体专用 AI 兴趣** | 10 类优先级 | `custom/ai/semiconductor.txt` 半导体产业链/AI算力/光通信/先进封装 | AI 筛选 → 50-80 候选 | 行业专项深度 |

> **关键洞察**：44 个 feed = **content-factory 的"选题金矿"**。每天 1139 条，AI 智能筛选后剩 50-80 条高质量候选。**之前 content-factory 自建的 bibi/RSS 系统可以退休**，全部用 TrendRadar。

**6 个微信公众号 → 5 个已恢复（2026/6/28 21:30 TrendRadar --now 跑通）**：
- ✅ `wechat-htzqcl` 华泰证券策略研究（10 条）
- ✅ `wechat-tfyanjiu` 天风研究（10 条）
- ✅ `wechat-bdtcygc` 半导体行业观察（10 条）
- ✅ `wechat-yckjpl` 远川科技评论（10 条）
- ✅ `wechat-kdcc` 看懂产业链（10 条）
- ✅ `wechat-zgzqb` 中国证券报（10 条）

→ 实际 6 个微信公众号全部恢复，rss_feeds 表从 44 → 50（+6），rss_items 从 1139 → 1302（+163 条）。

**剩余 1 个未拉通的 feed**：`ruanyifeng` 阮一峰的网络日志（RSSHub 路由问题，非公众号）。默认加入 `scripts/paused-channels.txt`，等用户验证 RSSHub `/ruanyifeng/weekly` 路由。

**扩展兴趣的方法**：
1. 改 `~/001_project/TrendRadar/config/ai_interests.txt` 加新方向
2. 跑 TrendRadar `python3 main.py --now` 触发 AI 重新分类
3. 等 10 分钟后看 `output/rss/YYYY-MM-DD.db` 新结果
4. 同步到本 SOP 4.1.1 映射表

### 4.2 研究（第 2 步，2-3 h）

> **2026/6/28 重构**：知识库二次总结丢失精度 → ZsxqCrawler 原始文件升 P0(必跑),research-reports /query 降级为可选(MOC 概念库)。

**素材来源优先级**：

| 来源 | 角色 | 用法 |
|---|---|---|
| 🥇 **ZsxqCrawler 原始导出**(新 P0) | **一手机构观点** | **Step 0 必跑**:扫文件 + 章节 grep + 段落读(详见 4.2.1) |
| 🥈 serenity-skill | 产业链深度 | 跑公告/财报/问询函(必跑) |
| 🥉 industry-kol-scan.py | 防漏标 | **Step 1.5 从发文前移到研究阶段**(详见 4.2.3) |
| 4️⃣ web_search | 2026 H1 数据 | 补最新数据 + 海外视角 |
| 5️⃣ cninfo-anns + myMCP | 公告 + 行情/估值 | 硬数据(必跑) |
| 6️⃣ research-reports /query | MOC 概念库 | **可选**:只查 MOC 主题/概念关联 |
| 7️⃣ bibigpt summarize --chapter | 音视频素材 | 选题灵感(TrendRadar 已覆盖大部分) |

#### 4.2.1 ZsxqCrawler 原始导出（Step 0，硬约束 · 2026/6/28 新增）

**为什么这条**：用户 6/28 核心洞察——**知识库二次总结会丢失精度**。ZsxqCrawler 是知识星球抓的**原始 .md 文件**(2895 条话题,2024-11 → 2026-06),保留作者/日期/ID/点赞/阅读量等完整元数据,是 content-factory 的**精度最高源**。文件结构:`MM-DD_<主题>.md`,每篇文章 5-15 个章节,章节里有具体观点/数字/公司名。

**强制 4 步**(写新文章前必跑):

1. **扫文件名**(粗筛主题相关)
   ```bash
   # 扫最近 3 个月 + 关键词
   rg -l "<关键词>" /Users/chenlei/002_tools/ZsxqCrawler/output/export_by_date/2026/
   # 例:rg -l "玻璃基板" /Users/chenlei/002_tools/ZsxqCrawler/output/export_by_date/2026/
   ```

2. **读章节标题 + 内容 grep**(精筛)
   ```bash
   # 在命中的文件里 grep 章节
   rg -n "<关键词>" /path/to/<file>.md
   # 例:rg -n "玻璃基板" 06-01_AI算力链更新.md
   # 返回:章节标题:行号 + 命中段落
   ```

3. **读章节前后 2-3 段**(拿完整观点)
   - 章节标题看起来像"总结",但**具体观点/数字藏在前后段落**
   - 例:章节标题"1)核心叙事:Token 经济学",但"6 兆晶体管 / 150 家供应链 / 台湾从一开始就和我们在一起"在前 2 段

4. **写进 frontmatter**(详见 4.3.7 A17 新字段)
   ```yaml
   zsxq_crawler:
     queried_at: "2026-06-25"
     found_files: 8
     cited_sections: 12
     citations:                # 引用列表(硬约束 ≥ 1)
       - file: "06-01_AI算力链更新.md"
         author: "乐晴"
         date: "2026-06-01"
         section: "1) 黄仁勋 GTC Taipei 2026 演讲要点总结"
         paragraph: "Vera Rubin 全面量产确认..."
   ```

**降级处理**:如果 ZsxqCrawler 无相关内容,在 frontmatter 加 `zsxq_crawler.queried_at` + `zsxq_crawler.found_files: 0` 标记,而不是跳过不扫。

**实战案例**(glass-substrate / glass-bridge-cpo):
- 扫"玻璃基板" + "玻璃桥" → 命中 15+ 文件(2025-12 → 2026-06)
- 章节 grep → 锁定关键观点(如"帝尔激光面板级 TGV 设备出货")
- 引用格式:`[来源:ZsxqCrawler 2026-04-15 / 国泰海通电子 / 第 3 节 / 段落 2]`

#### 4.2.1b research-reports /query 降级为可选（2026/6/28 修改）

**为什么降级**：知识库二次总结会丢失精度,直接读 ZsxqCrawler 原始比查 knowledge MOC 更准。

**保留用途**(仅作为概念索引,不是数据源):
- 查主题 MOC 索引(`wiki/moc/` 的概念关联)
- 查历史概念背景(已发 9 篇的复用)
- 查跨主题概念(`玻璃基板 ↔ 玻璃桥 ↔ CPO`)

**不再作为数据源**:
- ❌ 不再用 `linked_concepts` 里的"摘要"作为正文引用
- ❌ 不再用 `linked_sources` 里的"摘要"作为论据
- ✅ 改用 ZsxqCrawler 原文段落作为引用

**frontmatter 软提示字段**(从硬约束改为软提示):
```yaml
research_reports:
  queried_at: "2026-06-25"           # 软提示(留作溯源用)
  found_concepts: 12                 # 软提示(0 命中也允许)
  read_concepts: 8                   # 软提示
  linked_concepts:                   # 软提示(可空)
    - name: "AI电力"
      path: "wiki/concepts/AI电力.md"
      used_for: "电力板块定位"
```

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

#### 4.3.6 research_reports 查证记录（frontmatter 软提示 · 2026/6/28 软化）

**为什么软化**：用户 6/28 核心洞察——知识库二次总结丢失精度 → ZsxqCrawler 原始导出成为**新的硬约束**,research_reports 降级为**概念索引软提示**。

**frontmatter 软提示字段**（不再硬 FAIL）：

```yaml
research_reports:
  queried_at: "2026-06-25"           # 软提示(留作溯源,不再 ≤ 30 天硬约束)
  found_concepts: 12                 # 软提示(0 命中也允许)
  read_concepts: 8                   # 软提示
  linked_concepts:                   # 软提示(可空,仅作为概念索引)
    - name: "AI电力"
      path: "wiki/concepts/AI电力.md"
      used_for: "电力板块定位 + 4 大赛道画像"
  skipped_reason: ""                 # 软提示
```

**正文中的引用**：仍用 Obsidian 双链 `[[概念名]]` 格式(让 Obsidian 用户能跳转),但**不再作为论据**——论据改用 ZsxqCrawler 原始导出。

#### 4.3.7 🆕 zsxq_crawler 查证记录（frontmatter 硬约束 · 2026/6/28 新增）

**为什么是硬约束**：ZsxqCrawler 原始导出是 content-factory **精度最高源**(2895 条话题,完整保留作者/日期/ID/点赞/阅读量),每篇深度文**必须基于至少 1 条原始观点**,否则属于"凭印象写"。

**frontmatter 硬约束字段**：

```yaml
zsxq_crawler:
  queried_at: "2026-06-25"           # ZsxqCrawler 扫描时间,距今 ≤ 30 天(硬约束)
  found_files: 8                     # 命中的 .md 文件数
  cited_sections: 12                 # 引用章节数(硬约束 ≥ 1)
  cited_paragraphs: 35               # 引用段落数
  citations:                          # 引用列表(必填 ≥ 1)
    - file: "06-01_AI算力链更新.md"
      author: "乐晴"
      date: "2026-06-01"
      section: "1) 黄仁勋 GTC Taipei 2026 演讲要点总结"
      paragraph: "Vera Rubin 已投入全面量产..."
      quote: "台湾从一开始就和我们在一起"
  skipped_reason: ""                 # found_files = 0 时必填
```

**正文引用格式**：
```
[来源:ZsxqCrawler 2026-06-01 / 乐晴 / 第 1 节"黄仁勋 GTC Taipei 2026 演讲要点总结" / 段落 3]
```

**自动化检查**（compliance-check.py 加 A17b）：
- `zsxq_crawler.queried_at` 距今 ≤ 30 天 → FAIL
- `zsxq_crawler.cited_sections` ≥ 1 → FAIL
- `zsxq_crawler.citations` ≥ 1 项 → FAIL
- 任何一条 FAIL → publish --strict 拒绝发布

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