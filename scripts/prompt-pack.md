# scripts/prompt-pack.md
# Serenity + 公众号深度文 Prompt 模板库

## 1. Serenity-skill 跑研究 prompt

### 1.1 主题研究（深调研）

```
用 serenity-skill 深度调研 {topic} 的产业链。
请联网查公告、财报、问询函、互动易、招投标、环评/能评、
专利、客户认证和财务质量，先排产业链层级，
再找 5 个最值得优先研究的标的，
并说明卡住的环节、产业链位置、证据、排序理由和主要风险。
输出 markdown 格式。
```

### 1.2 单公司挑战

```
用 serenity-skill 挑战 [公司名/股票代码]。
它到底卡在哪一层？证据够不够？市场可能高估了什么？
什么情况说明这个判断应该降级？
```

### 1.3 多公司对比

```
用 serenity-skill 帮我研究最近 {方向}。
先拆产业链，再判断哪些环节更接近真实供需瓶颈，
最后给出股票和基金方向的优先研究清单。
```

## 2. v2 文章框架 prompt（公众号深度文）

```
基于以下素材，写一篇 6000-7000 字的公众号深度文。

## 主题
{title}

## 核心观点
{core_view}

## v2 强制要求
- 候选公司 ≥ 20 个，按 Controls/Supplies/Benefits/Weak/Story 5 分类
- Top 7 候选每个含 5 要素：环节/位置/原因/证据/风险
- 反共识方向 ≥ 3 类
- 数据时效：2026 H1 最新
- 数据源用最新版报告（IEA《Energy and AI》2025 等）

## 素材
{research_data}

## 结构（按 templates/post-template-v2.md）
1. 核心观点 + 证据等级
2. 为什么现在写这个
3. 主流叙事 vs 我的判断
4. Serenity 8 层级（表格）
5-7. 三大卡点深度分析
8. 公司 5 分类
9. 优先研究 Top 7（5 要素）
10. 反共识判断
11. 个人判断（zettaranc 1 段）
12. 风险 + 升降级信号
13. Serenity 研究动作清单
14. 一图收尾
15. 免责声明

## 输出要求
- 标题 ≤ 30 字，含反共识钩子
- 字数 8,000-10,000 字符
- 每条强结论标证据等级（🟢🟡🔴）
- 所有数据标日期和来源
- 涉及具体公司时标注"研究案例 / 不构成推荐"
- 不出现"目标价/推荐/保证/加仓"等高风险词（除非在免责声明反向表达）
```

## 3. mmx 封面 prompt 模板

### 3.1 投研风（推荐）

```
Editorial cover image for Chinese investment research article,
inspired by Bloomberg Terminal, Reuters Breakingviews and 远川研究所 cover style.
Topic: {topic}
Visual: deep charcoal background (#0f1419) with single bold accent color burnt orange (#d97706),
minimal composition featuring an abstract data visualization — a horizontal price curve rising
against a backdrop of circuit-board grid lines and abstract mineral crystal silhouettes at the bottom.
Editorial photography meets data dashboard.
Moody, sophisticated, professional.
No text, no human faces, no logos.
Cinematic quality, sharp focus.
```

### 3.2 机器人 / 科技主题

```
Editorial cover image for Chinese investment research article, inspired by Bloomberg Terminal style.
Topic: humanoid robot industry chain, China-Korea comparison, embodied AI.
Visual: deep charcoal background with burnt orange accent, abstract composition featuring
humanoid robot silhouette emerging from circuit patterns and gear mechanisms,
data visualization elements suggesting production cost curves declining, editorial sophistication.
No text, no human faces. Cinematic quality, sharp focus.
```

## 4. matplotlib 图表 prompt（数据描述）

### 4.1 8 层级横向条形图

```
生成 AI 算力产业链 8 层级扩产难度排序的横向条形图。
深色背景 (#0f1419)，每行一个层级，宽度按扩产难度 0-1。
L7/L8 用红橙色突出，标注"◆ 卡点"。
```

### 4.2 卡点矩阵散点图

```
生成 AI 算力 8 层级的卡点矩阵散点图。
横轴=扩产难度（0-1），纵轴=估值预期（0-1）。
象限用虚线分隔，第四象限（高难度+低预期）标注"◆ 被低估的卡点"。
数据点按 Serenity 5 分类着色：红=Controls / 橙=Supplies / 蓝=Benefits / 紫=Weak。
```

### 4.3 价格走势折线图

```
生成 {品类} 价格走势的折线图（{时间范围}）。
深色背景，关键节点用箭头标注（高点 / 急跌 / 现价）。
数据来源标注在标题下方。
```

## 5. 合规检查 prompt

> 完整 14 项清单见 `templates/compliance/checklist.md`(SOP 的唯一权威来源)。
> 每次发布前,把全文 + 本清单喂给模型做二次审稿:

```
请按 templates/compliance/checklist.md 的 14 项(7 项内容硬约束 + 7 项合规与证据)
逐项检查下面这篇文章,输出每项 PASS / FAIL + 缺失项的修改建议。

【A. 内容硬约束】
1. 标题 ≤ 30 字 + 反共识钩子
2. 候选公司 ≥ 20 个,5 分类齐全
3. 9.4 / 9.5 两类有具体代码(不是 `...` 或类别描述)
4. Top 7 完整 5 要素
5. 反共识方向 ≥ 3 类
6. 配图 ≥ 5 张(matplotlib 数据图)
7. 数据时效 2026 H1 最新

【B. 合规与证据】
8. 免责声明(中版本)
9. 证据等级 🟢🟡🔴 齐全
10. 强结论有可查来源
11. 高风险词(目标价/推荐/保证/加仓/稳赚/必涨/必跌)0 处误用
12. 短期判断有时间窗口
13. 升降级信号 ≥ 3 条 + ≥ 3 条(用段落锚点)
14. tracking/predictions/{slug}.json 已写入(发布后自动跑)

文章全文:
<贴文章>
```

输出格式:
```
✅ A. 内容硬约束: 7/7
✅ B. 合规与证据: 7/7
[如有 FAIL] 修改建议:
- 项 X: <具体修改方法>
```