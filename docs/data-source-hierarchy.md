# content-factory 数据源层级图(主要 / 验证 / 理论支撑)

> **创建日期**:2026-06-28
> **目的**:content-factory 当前有 11 个数据源,职责重叠。用 3 类层级梳理:**主要数据源**(写文章主要用)+ **验证数据源**(交叉验证/披露)+ **理论支撑**(背景/方法论)。
> **维护**:加新数据源时,在对应类别加一行;写文章时按这个表选源。

---

## 一、3 类层级速览

| 类别 | 数量 | 用途 | 出现位置 |
|---|---|---|---|
| 🟢 **主要数据源** | 6 个 | 写文章**主要依据**(行情/公告/调研/技术/选题/趋势) | 正文数据 + Step 3 + 5 分类表 |
| 🟡 **验证数据源** | 3 个 | 交叉验证 / 披露合规 / 反共识溯源 | A16 data_verified + 反共识 5/6 |
| 🔵 **理论支撑** | 2 个 | 背景 / 历史 / 方法论 | 概念框架 + MOC + 引言 |

---

## 二、🟢 主要数据源(写文章主要用)

### 1. myMCP (Tushare 兼容接口 · 258 工具)
- **位置**:mavis MCP 服务,URL `https://fast.xiaodefa.cn/mcp/?token=...`
- **数据域**(8 大域):沪深股票(行情/财务/资金)/板块/沪深港通/宏观/海外/研报
- **写文章用法**:
  - **每日数据快照**:myMCP daily + daily_basic(`ts_code` + `trade_date=20260626`)
  - **公司估值**:daily_basic(`pe` / `pe_ttm` / `pb` / `total_mv` / `circ_mv`)
  - **资金流向**:moneyflow / moneyflow_hsgt
  - **港股 + 美股**:hk_daily / us_daily(备选)
- **使用门槛**:要 mavis token
- **替代**:cninfo(部分行情)、wind(付费)
- **注意事项**:`daily` 多 ts_code 一次调用 502,**必须逐家重试 3 次**(单元化记录在 memory)
- **示例**:`mavis mcp call myMCP daily '{"ts_code":"600487.SH","trade_date":"20260626"}'`

### 2. cninfo 巨潮(免费无限 API · scripts/cninfo-anns.py)
- **位置**:本地脚本,调用巨潮公开 API
- **数据域**:上市公司公告(治理变动/分红/减持/问询/收购/破产)
- **写文章用法**:
  - **A16 data_verified.verified_sources**:每条公告带 URL,合规硬要求
  - **风险信号**:异动公告 / 风险提示 / 立案调查 / 实控人变更
  - **治理变动**:董事辞职 / 财务总监变更 / 控股股东质押 / 分拆上市
  - **监管信号**:交易所问询函 / 监管警示函 / 立案
- **使用门槛**:0
- **替代**:东方财富 / 同花顺(付费)
- **示例**:`python3 scripts/cninfo-anns.py --ts-code 600487.SH --days 14 --json`

### 3. web_search(原生工具 + matrix MCP · web_search)
- **位置**:原生 web_search 工具 / matrix MCP server `web_search`
- **数据域**:全网搜索(中文/英文 / 媒体 / 学术 / 政府)
- **写文章用法**:
  - **Step 3 industry-kol-scan**:防漏标防御(扫描 15 条结果 + A 股白名单过滤)
  - **技术验证**:TGV 工艺 / FAU vs 玻璃波导 / 蛛网模型 等技术细节
  - **媒体观点**:大摩 / 中金 / 红杉 等投研机构观点
  - **海外视角**:英伟达 / TSMC / 康宁 等海外公司动态
- **使用门槛**:matrix MCP 工具可能 `Tool not supported by this cli version`,用原生 `web_search` 替代
- **替代**:手工 google / bing(无法批量)
- **示例**:`web_search "玻璃基板 6 大环节" 2026`

### 4. TrendRadar(用户自建热点雷达 · v6.10.0 + MCP v4.1.0)
- **位置**:`/Users/chenlei/001_project/TrendRadar/`
- **数据域**:40+ RSS 源 + 20+ 热榜平台 + AI 智能筛选(15 类兴趣)
- **写文章用法**:
  - **选题库**:`output/rss/YYYY-MM-DD.db` 看今日 AI 筛选 Top 20
  - **5 个微信公众号独家**:华尔街见闻 / 半导体产业纵横 / TMT 研究院 / 产业投研院 / 大宗商品
  - **机构视角深度报告**:每天 30-50 条,AI 智能筛选后剩 5-10 条
- **使用门槛**:TrendRadar 服务需要跑(本地 + docker)
- **替代**:`scripts/rss-feed.py`(10 频道,已被 TrendRadar 完全覆盖,可退休)
- **示例**:见 `docs/ai-interests-mapping.md` 的 Python 脚本
- **重要性**:**content-factory 的"上游选题源"**,比 bibi/RSS 强 10 倍

### 5. research-reports /query(知识库 · 1053 概念 + 2181 飞书日报)
- **位置**:`~/003_knowledge/knowledge_base/research-reports/`
- **数据域**:你长期积累的高质量原料
  - `wiki/concepts/` — 1053 个概念文件(如 玻璃基板.md / TGV.md / HBM-高带宽存储器.md)
  - `wiki/sources/` — 2181 个飞书日报(如 摘要-2026-06-25-ai链更新-玻璃桥玻璃基板.md)
- **写文章用法**:
  - **A17 research_reports 必跑**:每篇文章 frontmatter 必填,命中的概念 + linked_concepts
  - **正文双链 `[[概念名]]`**:Obsidian 用户可直接跳转
  - **Step 0 研究**:`scripts/research-reports-query.sh "<主题>"` 找相关概念
- **使用门槛**:0(本地路径)
- **替代**:手工 web_search(效率低 10 倍)
- **示例**:`bash scripts/research-reports-query.sh "CPO 玻璃桥"`

### 6. bibi / B 站音视频(50 条/天 · scripts/bibi-safe.py + scripts/bibi)
- **位置**:本地脚本,调用 bibigpt API
- **数据域**:B 站 UP 主 + 部分 YouTube 频道(50 条/天,30 分钟额度)
- **写文章用法**:
  - **音视频内容抓取**:bilibili UP 主闭门会(摩根士丹利/中金/红杉等)
  - **字幕 + 总结**:用 bibigpt 总结视频要点
- **使用门槛**:**额度限制**(pro 100 分钟/月,5/5 hallucination)
- **替代**:
  - **TrendRadar 已经覆盖**(B 站 UP 主列表对比见 `docs/ai-interests-mapping.md`)
  - **建议退休**,只作为备用
- **注意事项**:**Hallucination 100%**(5/5 次返回 LLM 编造内容),所有 summarize 必须走 bibi-safe.py 检查

---

## 三、🟡 验证数据源(交叉验证/披露合规)

### 7. industry-kol-scan.py(Step 3 行业情报扫描)
- **位置**:`scripts/industry-kol-scan.py`
- **数据域**:web_search 结果 → A 股白名单过滤 → 候选公司清单
- **用法**:
  - **Step 3 防漏标**:发文前必跑,扫出 Top 7 之外的漏标公司
  - **反共识 5/6**:作为反共识补丁的"漏标公司"数据源
- **角色**:**验证**(主流程 A2 候选公司是否覆盖完整)
- **限制**:
  - 正则提取可能漏掉不以"公司/股份"结尾的名字(已扩 8 类后缀)
  - 白名单过滤会过滤掉非 A 股真正龙头(用 `scripts/non-a-stock-participants.md` 登记)

### 8. myMCP 港股 + 美股(同源)
- **位置**:myMCP `hk_daily` / `us_daily` / `hk_fina_indicator`
- **数据域**:港股 + 美股 + 美元指数 + 海外宏观
- **用法**:
  - **海外公司估值**:美光(MU.US)/ 英伟达(NVDA.US)/ 康宁(GLW.US) 等
  - **对比参考**:A 股公司 vs 海外对标公司估值
- **角色**:**验证**(A 股龙头 vs 全球同行的差距)

### 9. data-updated / cninfo 公告对比
- **位置**:`drafts/raw/<slug>/cninfo/missing-*.json`
- **数据域**:公告 + 治理变动 + 监管信号
- **用法**:
  - **反共识 5/6 漏标公司**:从 cninfo 公告拿治理信号(分拆/辞职/立案)
  - **合规 A16**:frontmatter verified_sources 必填
- **角色**:**验证**(主流程 myMCP 数据的真实性)

---

## 四、🔵 理论支撑(背景/方法论)

### 10. SOP.md + docs/ 文档(content-factory 内部)
- **位置**:`SOP.md` / `docs/cn-pub-style-guide.md` / `docs/ai-interests-mapping.md`
- **数据域**:content-factory 自身的流程文档
- **用法**:
  - **写作流程**:SOP 4.1-4.5 选题→研究→写作→配图→发布
  - **公众号样式**:10 条规则
  - **数据源映射**:15 类兴趣 × 9 大主题
- **角色**:**理论支撑**(写文流程的方法论)

### 11. obsidian-vault(本地 Obsidian 库 · research-reports 之外)
- **位置**:`~/Documents/Obsidian/` 或类似路径(用户具体路径)
- **数据域**:你的个人笔记 / MOC / 投资框架(zettaranc 等)
- **用法**:
  - **个人框架**:zettaranc 极简版(占文章 ≤ 10%)
  - **MOC 主题**:配合 SOP 4.1 选题原则
- **角色**:**理论支撑**(个人框架)

---

## 五、数据流(从选题到发布的全流程)

```
┌──────────────────────────┐
│ 1️⃣ 选题 (SOP 4.1 + 4.1.1) │
│  🟢 TrendRadar AI 筛选     │
│  🟢 bibi 50 条/天(可选)    │
│  🟢 research-reports /query │
│  🟡 industry-kol-scan.py   │
│  🔵 SOP + 5 问过滤          │
└──────────┬───────────────┘
           ↓
┌──────────────────────────┐
│ 2️⃣ 研究 (SOP 4.2)         │
│  🟢 myMCP daily + 公告     │
│  🟢 cninfo 公告             │
│  🟢 web_search 技术验证    │
│  🔵 research-reports 概念  │
│  🟡 港股美股对比(海外对标)  │
└──────────┬───────────────┘
           ↓
┌──────────────────────────┐
│ 3️⃣ 写作 (SOP 4.3)         │
│  🟢 5 大分类 20 家 A 股      │
│  🟢 反共识 ≥ 3              │
│  🟢 TL;DR 摘要卡片          │
│  🟢 11 章节钩子              │
│  🟡 A16/A17 合规验证        │
│  🔵 zettaranc 极简版         │
└──────────┬───────────────┘
           ↓
┌──────────────────────────┐
│ 4️⃣ 美化 (cn-pub-beautify)  │
│  规则 1 TL;DR              │
│  规则 2 关键数字加粗        │
│  规则 5 风险 emoji         │
│  规则 6 数据快照           │
│  规则 8 章节钩子            │
│  规则 10 中英数字间距        │
└──────────┬───────────────┘
           ↓
┌──────────────────────────┐
│ 5️⃣ 发布 (publish.sh)      │
│  compliance-check --strict │
│  MD + 图 + 封面 + 归档      │
│  tracking 自动登记          │
│  发布说明 v2 专属版         │
└──────────────────────────┘
```

---

## 六、优先级与备份

### 写文时数据源选用决策

```
Q1: 文章数据(估值/股价/市值)用什么?
   A: myMCP daily + daily_basic (主)
      cninfo 公告 (验证治理变动)

Q2: 文章选题从哪里来?
   A: TrendRadar AI 筛选 (主)
      bibi 50 条/天 (备选,已被 TrendRadar 覆盖)
      web_search Step 3 (验证漏标)

Q3: 文章概念/历史用什么?
   A: research-reports /query (主)
      Obsidian 个人库 (个人框架)

Q4: 文章海外视角用什么?
   A: web_search (主)
      myMCP hk/us_daily (验证估值)

Q5: 文章合规用什么?
   A: cninfo 公告 (主,A16 必填)
      industry-kol-scan.py (验证漏标)
```

### 一个挂了用什么替代

| 主数据源挂了 | 替代方案 |
|---|---|
| myMCP | cninfo(部分行情)+ web_search(技术) |
| cninfo | web_search + myMCP(部分公告字段) |
| web_search | 直接 google 手动搜 + TrendRadar AI 筛选 |
| TrendRadar | bibi 50 条 + research-reports 飞书日报 + web_search |
| research-reports | web_search 飞书日报来源 + Obsidian 个人库 |
| bibi | TrendRadar(完全覆盖 B 站 UP 主)+ web_search |

---

## 七、5 个微信公众号(TrendRadar 独家 · 内容金矿)

| feed_id | 公众号 | 每日条数 | 关联 TrendRadar 兴趣类 |
|---|---|---|---|
| `wechat-wsj` | 华尔街见闻 | 10 | 3 + 7 + 8 |
| `wechat-bdt` | 半导体产业纵横 | 10 | 4 |
| `wechat-tmt` | TMT 研究院 | 10 | 3 + 4 + 6 |
| `wechat-cytouyan` | 产业投研院 | 10 | 4 + 6 |
| `wechat-dzsp` | 大宗商品价值投资俱乐部 | 0-5 | 13 + 14(消费品,不写) |

**重要性**:**bibi/RSS 抓不到微信公众号**,这是 TrendRadar 独家价值。

---

## 八、维护说明

### 加新数据源时

1. 在对应类别加一行
2. 标注:**位置 / 数据域 / 写文章用法 / 使用门槛 / 替代 / 注意事项 / 示例**
3. 同步更新第 5 节数据流 + 第 6 节备份表

### content-factory 数据流变化时

1. 更新第 5 节"数据流"图
2. 更新第 6 节"决策树"

### 选题库扩展时

1. 看 `docs/ai-interests-mapping.md` "选题库"
2. 加新选题 → 标注触发源(必须对应某个主要数据源)

---

## changelog

- **2026-06-28**:v1,基于第 9 篇发布 + TrendRadar 项目发现,梳理 11 个数据源为 3 类层级