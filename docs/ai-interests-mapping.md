# TrendRadar AI interests ↔ content-factory 主题映射

> **创建日期**:2026-06-28
> **维护人**:Mavis
> **目的**:把 TrendRadar 的 15 类投资兴趣(`config/ai_interests.txt`)跟 content-factory 9 大主题做映射,让选题不重复、不漏点。

---

## 数据流

```
TrendRadar (40+ RSS + 20+ 平台 + AI 智能筛选)
   ↓ output/rss/YYYY-MM-DD.db
   ↓ ai_interests.txt 15 类兴趣
content-factory
   ↓ 看今日 AI 筛选 Top 20
   ↓ 跟 9 大主题对照
   ↓ 选候选 → 5 问过滤 → 写文
```

---

## 15 类兴趣 × 9 大主题 映射表

### TrendRadar 15 类(按 ai_interests.txt 顺序)

| # | 兴趣类 | 已发 9 篇覆盖 | 选题库(5 个) | 空白 / 待补 |
|---|---|---|---|---|
| 1 | 中国科技与互联网公司 | 第 6 篇 + 第 1-2 篇部分 | — | 京东战略 / 字节产品节奏 |
| 2 | 大模型与 AI 产品 | 第 6 篇部分 | **选题 5 China Coding** | Qwen / GLM 详细对比 |
| 3 | AI 基础设施与云算力 | 第 6-9 篇 + 第 7 篇 | **选题 1 AI Memory + 选题 2 Token 算租** | — |
| 4 | 芯片与半导体制造 | **第 7/8/9 篇(强项)** | — | HBM / ASIC / 算力金属 |
| 5 | 智能汽车与自动驾驶 | 第 1 篇部分 | — | 比亚迪出海 / FSD 中国落地 |
| 6 | 机器人与具身智能 | 第 4 篇 | **选题 4 灵巧手 2.0** | — |
| 7 | 全球科技巨头 | 第 6 篇部分 | — | OpenAI vs Claude 财报 |
| 8 | 地缘政治与国际关系 | 第 8 篇部分 | — | 中美 AI 芯片管制升级 |
| 9 | 金融市场与宏观政策 | 第 7 篇部分 | — | 美元降息对科技股影响 |
| 10 | 能源与电力系统 | **第 5 篇** | — | 雅鲁藏布江 / 核电重启 |
| 11 | 航天与深空探索 | 未覆盖 | **选题 3 商业航天** | — |
| 12 | 前沿科学技术 | 未覆盖 | — | 量子计算商用化 |
| 13 | 文化 IP 与内容产业 | 不写 | — | 跨度过大 |
| 14 | 零售与消费品牌 | 不写 | — | 跨度过大 |
| 15 | 国家与区域观察 | 间接覆盖 | — | — |

---

## content-factory 9 大主题(已发 9 篇)

| # | slug | 主题 | TrendRadar 兴趣类 | 关联微信公众号 |
|---|---|---|---|---|
| 1 | morgan-ai-supply-chain | AI 真正的瓶颈不是 GPU(电力/稀土/铜) | 3 + 9 + 10 | TMT / 产业投研院 |
| 2 | cicc-ai-population | 人形机器人真正的卡点不在本体 | 6 | TMT |
| 3 | asean-ai-supply-chain | AI 供应链全球化分工(中国卡上游/东盟卡中下游) | 1 + 3 | TMT |
| 4 | ai-three-bottlenecks | AI 算力三大瓶颈(电力/氦气/内存) | 3 + 4 | 半导体产业纵横 |
| 5 | ai-gpu-power-mlcc | AI 算力下半场 3 个被低估的新卡点 | 3 + 4 | 半导体产业纵横 / 产业投研院 |
| 6 | electric-power | 夏炒电 4 大赛道真相 | 10 | TMT |
| 7 | liquid-cooling | AI 数据中心液冷(算力第 4 大卡点) | 3 + 4 | 半导体产业纵横 |
| 8 | glass-substrate | AI 芯片先进封装"新底座"玻璃基板 6 大环节 | 4 | 产业投研院 |
| 9 | glass-bridge-cpo | 康宁 GlassBridge + 1300 亿 CPO 光互连新空间 | 3 + 4 | 产业投研院 / TMT |

---

## 选题库(5 个待开干)

| 选题 | TrendRadar 触发源 | 对应兴趣类 | content-factory 接续 |
|---|---|---|---|
| **1. AI Memory Crunch** | 半导体产业纵横 "HBM 急需散热" + 华尔街见闻 "美光长协 220 亿" + Bloomberg "AI Memory Crunch" | 3 + 4 | 接第 3 篇 ai-three-bottlenecks |
| **2. Token 算租** | 产业投研院 "算力租赁+独家壁垒,5 家公司" + 飞书日报 6/25 "AI 链更新-token 算租" | 3 | 完全新方向 |
| **3. 商业航天** | TrendRadar AI interests #11 + 飞书日报 6/25 "商业航天更新" | 11 | 完全新方向 |
| **4. 灵巧手 2.0** | TrendRadar AI interests #6 + 飞书日报 6/25 "物理 AI 人形机器人更新" | 6 | 接第 4 篇 cicc-ai-population |
| **5. China Coding** | All-In Pod 6/27 "China Catches Up in Coding" + Bloomberg 6/27 "China Coding" | 2 | 完全新方向 |

---

## TrendRadar 5 个微信公众号独家信号

> **关键洞察**:这 5 个微信公众号 = **content-factory 的"选题金矿"**。bibi/RSS 抓不到。
> 每天 30-50 条深度报告,AI 智能筛选后剩 5-10 条高质量候选。

| feed_id | 公众号 | 内容方向 | 每日条数 |
|---|---|---|---|
| `wechat-wsj` | 华尔街见闻 | 全球宏观 + 美股 + 半导体 + 中国财经 | 10 |
| `wechat-bdt` | 半导体产业纵横 | 半导体产业链深度报告(国产替代/光刻机/先进封装) | 10 |
| `wechat-tmt` | TMT 研究院 | TMT 板块公司动态(光器件/算力金属/钨钼锂) | 10 |
| `wechat-cytouyan` | 产业投研院 | 行业深度 + 公司分析(电子布/算力租赁/光模块心脏) | 10 |
| `wechat-dzsp` | 大宗商品价值投资俱乐部 | 大宗商品 + 周期股(白酒/铜/油运/化工) | 0-5 |

---

## TrendRadar 数据查询脚本

### 今日 AI 筛选 Top 20

```bash
python3 << 'EOF'
import sqlite3
from datetime import date

db = f'~/001_project/TrendRadar/output/rss/{date.today().isoformat()}.db'
c = sqlite3.connect(db)
c.row_factory = sqlite3.Row

print("=== 今日 AI 筛选 Top 20 ===")
for r in c.execute('''
    SELECT i.title, i.url, f.name, af.score
    FROM rss_items i
    JOIN rss_feeds f ON i.feed_id = f.id
    LEFT JOIN ai_filter_analyzed_news af ON af.item_id = i.id
    WHERE af.score > 0.7
    ORDER BY af.score DESC LIMIT 20
'''):
    print(f'[{r["score"]:.2f}] [{r["name"][:20]}] {r["title"][:60]}')
EOF
```

### 微信公众号今天独家内容

```bash
python3 << 'EOF'
import sqlite3
from datetime import date

db = f'~/001_project/TrendRadar/output/rss/{date.today().isoformat()}.db'
c = sqlite3.connect(db)
c.row_factory = sqlite3.Row

wechat_ids = ['wechat-cytouyan', 'wechat-tmt', 'wechat-bdt', 'wechat-wsj', 'wechat-dzsp']
for r in c.execute(f'''
    SELECT i.title, f.name
    FROM rss_items i
    JOIN rss_feeds f ON i.feed_id = f.id
    WHERE f.id IN ({','.join(['?']*len(wechat_ids))})
    ORDER BY i.id DESC
''', wechat_ids):
    print(f'【{r["name"]}】 {r["title"][:60]}')
EOF
```

---

## 维护说明

### 加新主题(扩展兴趣)

1. 改 `~/001_project/TrendRadar/config/ai_interests.txt` 加新方向
2. 跑 TrendRadar `python3 main.py --now` 触发 AI 重新分类
3. 等 10 分钟看 `output/rss/YYYY-MM-DD.db` 新结果
4. 同步更新本文件 "选题库" 段落

### content-factory 发新文章后

1. 在本文件"content-factory 9 大主题"表加一行
2. 标"关联微信公众号"(必填)
3. 同步更新 SOP.md 4.1.1 映射表

---

## changelog

- **2026-06-28**:v1,基于第 9 篇发布后 + TrendRadar 项目发现,沉淀 15 类兴趣映射 + 5 个微信公众号 + 5 个待开干选题