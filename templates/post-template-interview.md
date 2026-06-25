# 公众号深度文模板 v3.0 · 访谈 / 对话专用

> **模板说明**：本模板是 v2 的扩展，**专为访谈 / 闭门会 / 高管对话**等对话驱动的深度文设计。
>
> **核心差异**（vs v2）：
> 1. **章节出处引用块**：每条陈立武 / 嘉宾原话必须有「章节 + 行号 + 中英对照」引用块
> 2. **中英对照标识**：用 🇺🇸 / 🇨🇳 emoji + **[EN]** / **[CN]** 标签 + 不同引用符号三重对比
> 3. **frontmatter 加 `interview:` 子字段**：记录嘉宾 / 主持人 / 来源 / 行号
> 4. **附录 A：引用块规范**：统一格式 + 强制位置 + 多源交叉要求
>
> **使用场景**：No Priors 播客 / 高管闭门会 / 业绩会 / 路演 / 行业大会 圆桌
>
> **基线**：保留 v2 所有 14 项硬约束（候选公司 ≥ 20 / 5 分类 / Top 7 5 要素 / 反共识 ≥ 3 / 配图 ≥ 5 / 证据等级三档 等）

---

## Frontmatter（v3 扩展）

```yaml
---
title: "<30 字，含反共识钩子>"           # v2 强制
subtitle: "<副标题，承接标题>"             # v3 新增
date: YYYY-MM-DD
slug: url-slug
tags: [主题1, 主题2, ..., serenity]
hook: "<50 字摘要，用于知乎答案开头>"
cover: images/cover.jpg

# ↓ v3 新增：访谈元信息 ↓
interview:
  guest: "Lip-Bu Tan（陈立武）"          # 嘉宾姓名 + 中文名
  host: "No Priors · Sarah Guo × Elad Gil"  # 主持 / 平台
  date: "2026 H1"                        # 录制时间
  source: "archives/2026-06/inter.md"    # 原文路径（用户存档）
  duration: "~60 分钟"                    # 访谈时长（可选）
  url: "（可选：原播客链接）"              # 原文链接（可选）

# ↓ 数据时效校验（A16 必读）============
# 每篇文章发布前必须 web_search 核验所有动态字段（股票代码 / 上市状态 /
# 营收 / 港股通 / ST 等），并在下面记录核验时间 + 来源。
# 详见 SOP.md 4.3.2.1「数据时效校验硬规则」
data_verified:
  verified_at: "YYYY-MM-DD"           # 最后一次 web_search 核验日期
  verified_by: "human | web_search"    # 谁核验的
  verified_sources:                    # 至少 1 个核验来源 URL
    - "https://..."
  verified_companies:                  # 核验过的公司清单（写代码 + 公司名）
    - "688795.SH 摩尔线程"

# ============ research-reports 查证记录（A17 必读）============
# 详见 SOP.md 4.2.1 + 4.3.6「research-reports /query 必跑」+「查证记录」
# v3 模板（访谈/对话）也需要先查 research-reports,补已有概念 + 飞书日报
research_reports:
  queried_at: "YYYY-MM-DD"             # /query 调用时间（必填,距今 ≤ 30 天）
  found_concepts: 0                    # 命中的概念数
  read_concepts: 0                     # 实际深度读的概念数
  linked_concepts:                     # 用到的概念（指向 ~/003_knowledge/...）
    - name: ""
      path: ""                         # 相对路径,如 wiki/concepts/AI电力.md
      used_for: ""
  linked_sources:                      # 用到的飞书日报 source
    - date: ""
      path: ""
      used_for: ""
  skipped_reason: ""
---
```

---

## 标题 + 开场引用

```markdown
# <主标题：≤ 30 字 + 反共识钩子>

> **核心引用 · 🚀 拯救英特尔 · 第 1-3 行**
> 
> 🇺🇸 **[EN]** *"I'm 66 and people that are, well, you should retire rather than taking on this hardest job in the industry. And so a couple reason. One is this iconic company, and it's so important for the semiconductor ecosystem and also so important for United States."*
> 
> 🇨🇳 **[CN]** 「我已经 66 岁了，总有人说'你应该退休了，何必还要承担这行里最苦的差事呢。'大致有几个原因。其中一家是这家极具标志性的公司，它对于半导体产业生态系统至关重要，对美国而言同样意义非凡。」
> 
> **证据等级**：🟢 L1（访谈原文）

![封面](images/cover.jpg)
```

### 📌 中英对照标识规范（核心规则）

| 维度 | 英文标识 | 中文标识 |
|---|---|---|
| **emoji 旗帜** | 🇺🇸 | 🇨🇳 |
| **标签** | **[EN]** | **[CN]** |
| **引用符号** | *" "*（双引号 / 美式英文标点） | 「」（直角引号 / 中文标点） |
| **嵌套引用** | > > 双重 blockquote | > 双重 blockquote |

**为什么用三重对比**：
- emoji 旗帜 → **视觉快速识别**（移动端友好）
- 文字标签 → **清晰不被误读**（任何渲染器都能识别）
- 不同引用符号 → **格式规范统一**（英文用 " "，中文用「」）

**保留 vs 修正**：
- 英文原话保留口误 / 未完成句子（"crarow" → "crawl"，不修正以保持原汁原味）
- 中文翻译修正口误 / 语法错误（让读者看懂）

---

## 第 1 节：证据等级说明（v2 保留 + v3 微调）

```markdown
> **本文证据等级说明**
> 
> - 🟢 **强证据**（L1）：访谈原文 + 公司财报 + 海关数据 + 监管文件
> - 🟡 **中证据**（L2）：访谈上下文推断 + 卖方研报 + 可信媒体
> - 🔴 **弱证据**（L3）：行业讨论 + 个人推测
> 
> 阅读建议：🟢 可直接参考，🟡 需对照多源，🔴 仅作线索。
> 
> **特别说明**（v3 新增）：本文核心证据来自 Lip-Bu Tan 在 No Priors 播客的访谈，每条强证据均带章节 + 行号 + 中英对照，可回原文追溯。
```

---

## 第 2 节：为什么现在写这个（v2 保留 + 必带引用块）

```markdown
## 一、为什么现在写这个

背景介绍 + 访谈核心来源 + 我们的研究角度。

> **访谈引用 · 🚀 拯救英特尔 · 第 28-32 行**
> 
> 🇺🇸 **[EN]** *"Nine of the ten company I invest halfway, they change their business square because market will change. So I like to have entrepreneur, a team, not just one person."*
> 
> 🇨🇳 **[CN]** 「我投资的十家公司里，有九家在中途都调整了业务方向，因为市场总是在不断变化。我更倾向于由创业者带领团队，而不是单打独斗。」
> 
> **证据等级**：🟢 L1（访谈原文）
```

---

## 第 3 节：主流叙事 vs 我的判断（v2 保留）

```markdown
## 二、主流叙事 vs 我的判断

**主流叙事**：xxx —— 来自市场共识。

**我的判断**：xxx —— 来自访谈 / 数据的反共识。
```

---

## 第 4 节：Serenity 式产业链 8 层级（v2 保留）

```markdown
## 三、Serenity 式 xxx 8 层级（细化版）

按 Serenity 方法：**先排产业链层级，再排国家承接度**。

![xxx 8 层级](charts/01-8layers.png)

| 层级 | 内容 | 技术壁垒 | 卡点定位 |
|---|---|---|---|
| L1 | xxx | 0.xx | - |
| ... | ... | ... | ... |
```

---

## 第 5-7 节：三个卡点（v2 保留 + 必带 ≥ 2 引用块 / 节）

```markdown
## 四、卡点 1：xxx —— xxx

### 数据 / 证据（≥ 2 个引用块）

> **访谈引用 · 🧠 AI 浪潮下的芯片机遇与瓶颈 · 第 88-89 行**
> 
> 🇺🇸 **[EN]** *"Couple of bottlenecks for the AI you demand and growth. One is of course, everybody knows power constraint, some country, the power they just don't have that it get impacted. And then secondly, a lot of people didn't realize the helium impact can be also quite significant for semiconductor. And then the thirdly is everybody know right now memory is a bigger shortage and everybody tried to scramble for memory."*
> 
> 🇨🇳 **[CN]** 「AI 需求和增长有几个瓶颈。首先，当然是大家都知道的电力限制……其次，很多人没有意识到氦气对半导体的影响也可能相当显著。第三，大家都知道现在内存短缺更为严重，每个人都在争抢内存。」
> 
> **证据等级**：🟢 L1（访谈原文）

> **独立信源交叉 · Gartner 2026/6/18**
> 
> 全球数据中心 2026 年耗电预测 **565 TWh**（同比 +26%）。
> 
> **证据等级**：🟢 L1（独立信源）

### 卡点逻辑

**判断**：...

---

## 五、卡点 2：xxx（重复"数据 / 证据 + 卡点逻辑"结构）

---

## 六、卡点 3：xxx（重复"数据 / 证据 + 卡点逻辑"结构）
```

---

## 第 8 节：公司 5 分类（v2 保留 + 关键公司带引用）

```markdown
## 七、公司 5 分类（Serenity 标准）

按 Serenity 框架，对 20+ 候选公司归类。

### 7.1 Controls the scarce layer（卡稀缺层）

| 公司 | 子行业 | 卡住环节 | 排序 | 访谈引用 |
|---|---|---|---|---|
| **Intel**（INTC） | CPU + EMT 封装 | 全球 CPU 龙头 / 先进封装挑战 TSMC | 🥇 #1 | 🚀 第 28-32 行 |
| **TSMC**（TSM） | 代工 | CoWoS 封装 / 14A 工艺 | 🥇 #2 | 🔬 第 121-122 行 |
| ... | ... | ... | ... | ... |

> **访谈引用 · 🔬 突破物理极限 · 第 121-122 行**
> 
> 🇺🇸 **[EN]** *"We all know about Cowart by tsmc. Now we have a really good one called emt that is a really next generation."*
> 
> 🇨🇳 **[CN]** 「我们都知道台积电的 CoWoS 封装。现在我们有一个非常好的叫做 EMT 的，是真正的下一代。」
> 
> **证据等级**：🟢 L1（访谈原文）

### 7.2 Supplies the scarce layer
（同上结构 + Controls + Supplies 各 ≥ 1 引用块）

### 7.3 Benefits from the trend
### 7.4 Has weak control
### 7.5 Mainly has a story
```

---

## 第 9 节：Top 7 五要素（v2 保留 + 每个公司带引用）

```markdown
## 八、优先研究名单（Top 7）：5 要素完整分析

按 Serenity 标准，每个 Top 候选给出 **卡住的环节 / 产业链位置 / 排序原因 / 证据 / 主要风险**。

### 🥇 #1 xxx（公司名）

- **卡住的环节**：xxx
- **产业链位置**：xxx
- **排序原因**：xxx
- **证据**：xxx
- **主要风险**：xxx

> **访谈引用 · 章节 · 第 X-X 行**
> 
> 🇺🇸 **[EN]** *"英文原话"*
> 
> 🇨🇳 **[CN]** 「中文翻译」
> 
> **证据等级**：🟢 L1（访谈原文）
```

---

## 第 10-13 节：反共识 / 个人判断 / 风险 / 动作清单（v2 保留）

```markdown
## 九、反共识判断

### 🔻 排名低的方向 1
### 🔻 排名低的方向 2  
### 🔻 排名低的方向 3

## 十、个人判断
## 十一、风险与升级/降级信号
## 十二、Serenity 研究动作清单
## 十三、一图收尾
```

---

## 附录 A：访谈引用块规范（**强制**）

### A.1 引用块模板

```markdown
> **访谈引用 · [章节名] · 第 X-X 行**
> 
> 🇺🇸 **[EN]** *"英文原话（保留原汁原味，包括口误和未完成句子）"*
> 
> 🇨🇳 **[CN]** 「中文翻译（修正口误 + 语法错误）」  
> 
> **证据等级**：🟢 L1（访谈原文）
```

### A.2 引用块位置 + 数量要求

| 位置 | 引用块数量 | 备注 |
|---|---|---|
| **开场 hook**（标题后） | ≥ 1 | 必带，设置文章调性 |
| **一、为什么写这个** | ≥ 1 | 介绍访谈来源 |
| **四 / 五 / 六、每个卡点** | ≥ 2 | 1 个访谈 + 1 个独立信源交叉 |
| **七、5 分类 Controls + Supplies** | 各 ≥ 1 | 引用对话中明确提到的公司 |
| **八、Top 7 每个公司** | ≥ 1 | 引用对话中嘉宾原话 |
| **九、反共识** | ≥ 1 | 引用对话中反共识判断 |
| **十一、风险信号** | ≥ 1 | 引用对话中关键判断 |

**总要求**：每篇 v3 模板文章**至少 10-12 个引用块**，分布均匀。

### A.3 章节标识符规范

| 章节 emoji | 章节名 | 访谈行号范围（示例） |
|---|---|---|
| 🚀 | 拯救英特尔：陈立武的经营之道 | 1-33 行 |
| 💰 | 强化根基：供应链与政府协作 | 35-47 行 |
| 🧠 | AI 浪潮下的芯片机遇与瓶颈 | 49-95 行 |
| 🔬 | 突破物理极限：新材料与新工艺 | 97-141 行 |
| 📈 | 投资哲学：从初创公司到长线思维 | 143-216 行 |
| 🔮 | 未来展望：物理 AI 与全栈解决方案 | 218-281 行 |

### A.4 中英对照标识规范（**核心规则**）

| 维度 | 英文标识 | 中文标识 |
|---|---|---|
| **emoji 旗帜** | 🇺🇸 | 🇨🇳 |
| **文字标签** | **[EN]** | **[CN]** |
| **引用符号** | *" "*（双引号 / 美式英文标点） | 「」（直角引号 / 中文标点） |
| **嵌套引用** | > > 双重 blockquote | > 双重 blockquote |

**为什么用三重对比**：
- emoji 旗帜 → **视觉快速识别**（移动端友好）
- 文字标签 → **清晰不被误读**（任何渲染器都能识别）
- 不同引用符号 → **格式规范统一**（英文 " "，中文「」）

### A.5 保留 vs 修正规则

| 元素 | 处理方式 |
|---|---|
| 英文口误（"crarow" → "crawl"） | **保留**（让读者感受原汁原味） |
| 英文未完成句 | **保留**（用 ... 表示） |
| 英文语法错误 | **保留**（不修正） |
| 中文翻译 | **修正**口误 + 语法 + 补充上下文 |
| 关键数字 / 公司名 | **精确翻译**，不简化 |

### A.6 多源交叉要求（**强结论必须**）

🟢 强结论必须有 ≥ 2 个独立信源：

| 信源类型 | 例子 |
|---|---|
| **访谈原文** | Lip-Bu Tan 原话 |
| **公司财报** | 2025 年报 / 季度公告 |
| **卖方研报** | 中信 / 华泰 / 花旗 / 大摩 |
| **行业协会** | GGII / APDCA / SEMI |
| **监管文件** | 工信部 / IMDA / SEC |
| **可信媒体** | Reuters / Bloomberg / FT |
| **其他高管访谈** | 同行 CEO / CTO 公开发言 |

**信源标注格式**：

```markdown
> **独立信源交叉 · Gartner 2026/6/18**
> 
> 全球数据中心 2026 年耗电预测 **565 TWh**（同比 +26%）。
> 
> **证据等级**：🟢 L1（独立信源）
```

### A.7 反向回溯

每条引用必须支持读者**回到原文**追溯：

- ✅ 章节名（英文章节标题）
- ✅ 行号（`archives/2026-06/inter.md` 文件的英文段落行号）
- ✅ 英文原话（直接引用，未修改）
- ✅ 中文翻译（修正口误）
- ✅ 证据等级（🟢 / 🟡 / 🔴）

---

## 附录 B：与 v2 模板的差异

| 维度 | v2 标准 | v3 访谈专用 |
|---|---|---|
| **字数** | 8000-10000 | 8000-12000（更长） |
| **候选公司** | ≥ 20 | ≥ 20 |
| **5 分类** | 齐全 | 齐全 |
| **Top 7 五要素** | 齐全 | 齐全 |
| **反共识方向** | ≥ 3 | ≥ 3 |
| **证据等级** | 🟢🟡🔴 三档 | 同 v2 |
| **配图** | ≥ 5 张 | ≥ 5 张 |
| **frontmatter** | 基础 6 字段 | 加 `interview:` 子字段（5 个） |
| **章节出处引用** | - | **≥ 10-12 个引用块 / 篇** |
| **中英对照** | - | **每条引用都做对比标识** |
| **多源交叉** | 建议 | **强结论必须** ≥ 2 信源 |
| **合规检查** | compliance-check.py 14 项 | 14 项 + A15（待定） |

---

## 附录 C：模板使用 checklist

写完后逐项打勾：

### C.1 Frontmatter

- [ ] `title` ≤ 30 字 + 反共识钩子
- [ ] `subtitle` 承接标题
- [ ] `interview.guest` 姓名 + 中文名
- [ ] `interview.host` 主持人 / 平台
- [ ] `interview.date` 录制时间
- [ ] `interview.source` 原文路径（用户存档）
- [ ] `tags` 含 serenity

### C.2 引用块（强制 ≥ 10-12 个）

- [ ] 开场 hook ≥ 1 个
- [ ] 一、为什么写这个 ≥ 1 个
- [ ] 四 / 五 / 六、每个卡点 ≥ 2 个
- [ ] 七、5 分类 Controls + Supplies 各 ≥ 1 个
- [ ] 八、Top 7 每个公司 ≥ 1 个
- [ ] 九、反共识 ≥ 1 个
- [ ] 十一、风险信号 ≥ 1 个

### C.3 引用块格式统一

- [ ] 每条引用带章节名（emoji + 中文标题）
- [ ] 每条引用带行号（第 X-X 行）
- [ ] 英文用 🇺🇸 **[EN]** *" "* 双引号
- [ ] 中文用 🇨🇳 **[CN]** 「」 直角引号
- [ ] 每条引用带证据等级（🟢 / 🟡 / 🔴）
- [ ] 强结论引用 + 独立信源标注

### C.4 14 项 v2 合规

- [ ] A1 标题 ≤ 30 字 + 反共识钩子
- [ ] A2 候选公司 ≥ 20
- [ ] A3 Weak/Story 有具体代码
- [ ] A4 Top 7 完整 5 要素
- [ ] A5 反共识方向 ≥ 3
- [ ] A6 配图 ≥ 5
- [ ] A7 数据时效 2026 H1
- [ ] B8 免责声明（中版本）
- [ ] B9 证据等级 🟢🟡🔴 齐全
- [ ] B10 强结论有可查来源
- [ ] B11 高风险词 0 误用
- [ ] B12 短期判断时间窗口
- [ ] B13 升降级信号齐全
- [ ] B14 tracking 记录已写入

---

## 附录 D：写作流程（v3 模板）

### 第 1 步：素材准备（已完成）

- [x] 原始口播稿存档（`archives/2026-06/inter.md`）
- [x] 中英对照翻译（已存档）
- [x] 总提纲（`drafts/raw/.../00-outline.md`）
- [x] 对话行业库（`drafts/raw/.../01-industry-library.md`）

### 第 2 步：交叉验证（每篇写作前必做）

- [ ] 用 web_search 验证关键事实（Trump 持股 / EMT 产能 / 氦气供应链）
- [ ] 用财报 / 公告补充关键数据
- [ ] 用其他信源做反共识对照

### 第 3 步：写正文

- [ ] 按本模板填空
- [ ] 每节 ≥ 1 个引用块（按 C.2 分布）
- [ ] 强结论必须配 ≥ 2 信源（按 A.6）

### 第 4 步：合规检查 + 发布

- [ ] `python3 scripts/compliance-check.py <slug> --strict` → 14/14 PASS
- [ ] `bash scripts/publish.sh <slug>` 一键打包
- [ ] `python3 scripts/tracking-record.py add <slug>` 记录预测

### 第 5 步：季度回看

- [ ] 6 个月后跑 `scripts/verify-predictions.py`
- [ ] 对照"升级 / 降级信号"验证 alpha

---

## 附录 E：合规检查脚本扩展（**待你拍板**）

v3 模板新增的"引用块规范"需要扩展 compliance-check.py。建议加：

### E.1 新增 A15 项

```python
def check_15_quote_citations(content, slug):
    """A15. 访谈类文章必须有引用块（≥ 10 个）+ 中英对照标识"""
    # 找所有引用块标记
    en_blocks = len(re.findall(r'🇺🇸 \*\*\[EN\]\*\*', content))
    cn_blocks = len(re.findall(r'🇨🇳 \*\*\[CN\]\*\*', content))
    citation_lines = len(re.findall(r'^\s*> \*\*访谈引用', content, re.MULTILINE))
    
    issues = []
    if citation_lines < 10:
        issues.append(f'引用块仅 {citation_lines} 个，需 ≥ 10 个')
    if en_blocks != cn_blocks:
        issues.append(f'🇺🇸 EN {en_blocks} 个 vs 🇨🇳 CN {cn_blocks} 个，不平衡')
    if en_blocks < 5 or cn_blocks < 5:
        issues.append(f'中英对照标识不足（EN {en_blocks} / CN {cn_blocks}）')
    
    if issues:
        return 'FAIL', '; '.join(issues)
    return 'PASS', f'引用块 {citation_lines} 个 + 中英对照 EN/CN 各 {en_blocks}/{cn_blocks}'
```

### E.2 同步 checklist.md

```markdown
- [ ] **15. 访谈类文章必须有引用块 + 中英对照**（≥ 10 个引用块 / 篇，EN 和 CN 标识平衡，详见 templates/post-template-interview.md 附录 A）
```

### E.3 publish.sh 自动启用

publish.sh 已集成 compliance-check.py，**新增 A15 自动生效，无需改 publish.sh**。

### E.4 是否启用？**等你拍板**

- 选项 1：启用 A15（更严，访谈类文章必须 ≥ 10 个引用块）
- 选项 2：不启用 A15（v2 标准继续用，引用块作为可选增强）
- 选项 3：warn 而非 fail（强制提示但不阻断）

---

## 附录 F：模板版本管理

| 版本 | 发布时间 | 适用场景 | 与 v2 关系 |
|---|---|---|---|
| v1 | 2026 Q1 | 入门级深度文 | 基线 |
| v2 | 2026 Q2 | 标准深度文（morgan / cicc / asean 用） | 升级版 |
| **v3** | **2026 Q3（即将）** | **访谈 / 对话驱动深度文** | **v2 + 引用块规范** |

**使用规则**：
- 普通深度文（基于行业研究 / 财报 / 监管文件）→ **用 v2**
- 访谈 / 闭门会 / 高管对话类 → **用 v3**

---

> **总结**：v3 模板 = v2 基线 + 章节出处引用块规范 + 中英对照标识 + 多源交叉要求。**保留 v2 14 项硬约束**，新增 A15（可选）。
> 
> **下一步**：拍板 4 个问题（写作顺序 / 第一篇主题 / 数据深度 / 是否启用 A15），开干第一篇。