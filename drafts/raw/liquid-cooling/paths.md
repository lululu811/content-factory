# liquid-cooling · 文件路径清单

> **用途**:快速查阅 liquid-cooling 第 7 篇文章涉及的所有文件路径
> **创建**:2026-06-25
> **Git commits**: `68fcd9f`(v1.0) + `b671027`(v1.1)

## 📊 5 张 matplotlib 信息图

### 源目录(画图脚本生成)

| 图 | 绝对路径 |
|---|---|
| 图 1 渗透率时间轴 | `~/content-factory/publish/images/liquid-cooling/charts/01-liquid-cooling-penetration.png` |
| 图 2 3 大液冷路线对比 | `~/content-factory/publish/images/liquid-cooling/charts/02-three-routes-comparison.png` |
| 图 3 芯片功耗 vs 散热方式 | `~/content-factory/publish/images/liquid-cooling/charts/03-chip-power-vs-cooling.png` |
| 图 4 单机柜功率密度演进 | `~/content-factory/publish/images/liquid-cooling/charts/04-rack-power-density.png` |
| 图 5 8 大龙头 Alpha 仪表盘 | `~/content-factory/publish/images/liquid-cooling/charts/05-alpha-dashboard.png` |

### 发布包(同步,sed `charts/` → `images/`)

| 图 | 绝对路径 |
|---|---|
| 图 1 | `~/content-factory/publish/final/liquid-cooling/images/01-liquid-cooling-penetration.png` |
| 图 2 | `~/content-factory/publish/final/liquid-cooling/images/02-three-routes-comparison.png` |
| 图 3 | `~/content-factory/publish/final/liquid-cooling/images/03-chip-power-vs-cooling.png` |
| 图 4 | `~/content-factory/publish/final/liquid-cooling/images/04-rack-power-density.png` |
| 图 5 | `~/content-factory/publish/final/liquid-cooling/images/05-alpha-dashboard.png` |

> **publish.sh 自动化**:第 70 行 `sed -i '' 's|charts/|images/|g'` 自动把 `charts/XX-xxx.png` 改成 `images/XX-xxx.png`,**不需要手动改**

## 📄 文本文件

| 类型 | 绝对路径 | 用途 |
|---|---|---|
| **正文** | `~/content-factory/drafts/posts/liquid-cooling.md` | 公众号深度文源文件(带 frontmatter) |
| **发布包 MD** | `~/content-factory/publish/final/liquid-cooling/liquid-cooling.md` | 去掉 `charts/` 改 `images/` 的最终发布版本 |
| **发布说明** | `~/content-factory/publish/final/liquid-cooling/发布说明.md` | publish.sh 自动生成的发布指引 |
| **outline** | `~/content-factory/drafts/raw/liquid-cooling/00-outline.md` | 选题大纲(章节设计 + 候选公司) |
| **gen-charts.py** | `~/content-factory/drafts/raw/liquid-cooling/gen-charts.py` | 5 张图生成脚本(可重跑) |
| **封面 image_001.jpg** | `~/content-factory/publish/images/liquid-cooling/cover-v2/image_001.jpg` | matrix_generate_image 生成的封面(SOP 4.3.4) |
| **封面 image_001.jpg(发布包)** | `~/content-factory/publish/final/liquid-cooling/images/cover-v2/image_001.jpg` | 同步到发布包 |
| **封面 image.jpg(发布包)** | `~/content-factory/publish/final/liquid-cooling/images/cover.jpg` | publish.sh 第 49 行自动复制 |
| **paths.md** | `~/content-factory/drafts/raw/liquid-cooling/paths.md` | 文件路径速查清单 |

## 🔗 同步到 research-reports

| 类型 | 绝对路径 | 来源 |
|---|---|---|
| **content-factory 摘要** | `~/003_knowledge/knowledge_base/research-reports/wiki/sources/2026-06-25-liquid-cooling-content-factory-summary.md` | scripts/sync-to-research-reports.py 自动生成 |
| **飞书日报原文** | `~/003_knowledge/knowledge_base/research-reports/wiki/sources/2026-06-25-AI链更新-液冷-PCB.md` | 乐晴 2026-06-25(用户附件,手动同步) |

## 📋 元数据

| 类型 | 绝对路径 | 备注 |
|---|---|---|
| **tracking 预测** | `~/content-factory/tracking/predictions/liquid-cooling.json` | 12 条预测(6 升级 + 6 降级),2026-12-22 验证日 |
| **git log** | `commit b671027` | liquid-cooling v1.1(乐晴飞书日报补充) |
| **git log** | `commit 68fcd9f` | liquid-cooling v1.0(首发,17/17 PASS) |

## 🔍 跨主题关联(由 dbs-content-system 自动建立)

| 关联主题 | 链接 |
|---|---|
| **electric-power**(L8 电力) | `~/content-factory/02-内容单元库/案例单元/CAS-20260625-006_电力L8卡点案例.md` |
| **ai-three-bottlenecks**(L5 HBM + 电力) | `~/content-factory/02-内容单元库/案例单元/CAS-20260625-015_电力L8基础瓶颈.md` |
| **ai-gpu-power-mlcc**(下半场卡点) | `~/content-factory/02-内容单元库/案例单元/CAS-20260625-019_功率半导体涨价传导.md` |
| **morgan-ai-supply-chain**(资源端) | `~/content-factory/02-内容单元库/案例单元/CAS-20260625-006_电力L8卡点案例.md` |

## 📂 关键命令速查

```bash
# 重跑 5 张图
python3 ~/content-factory/drafts/raw/liquid-cooling/gen-charts.py

# 合规检查(17 项)
python3 ~/content-factory/scripts/compliance-check.py liquid-cooling --strict

# 重新打包发布
bash ~/content-factory/scripts/publish.sh liquid-cooling

# 反向同步摘要到 research-reports
python3 ~/content-factory/scripts/sync-to-research-reports.py liquid-cooling

# 跑 research-reports /query 查液冷素材
bash ~/content-factory/scripts/research-reports-query.sh "液冷 数据中心"

# 查液冷相关概念 + source
ls ~/003_knowledge/knowledge_base/research-reports/wiki/concepts/ | grep -iE "液冷|aigc|aidc"
ls ~/003_knowledge/knowledge_base/research-reports/wiki/sources/ | grep -iE "液冷"
```

## 📊 5 张图示意

| 主题 | 核心信息 |
|---|---|
| 图 1 渗透率 | 2024 14% → 2026 40% → 2030 80%,AI 训练服务器 74%(工信部数据) |
| 图 2 路线对比 | 冷板 70% / 浸没 28% / 喷淋 2%,PUE 1.05 vs 1.15 vs 1.10 |
| 图 3 芯片功耗 | A100 400W → Rubin 2000W+,风冷上限 800W 多次被突破 |
| 图 4 机柜密度 | 2020 10kW → 2026 225kW(Vera Rubin NVL 72) |
| 图 5 Alpha 仪表盘 | 8 大龙头按 技术 + 客户 + 产能 三维评分 |

## 🔗 双向链接(内容工厂 ↔ research-reports)

```
research-reports
├── wiki/concepts/AI数据中心.md      ← liquid-cooling frontmatter linked
├── wiki/concepts/AI电力.md          ← liquid-cooling frontmatter linked
├── wiki/concepts/数据中心电源.md    ← liquid-cooling frontmatter linked
├── wiki/concepts/AIDC.md           ← liquid-cooling frontmatter linked
├── wiki/concepts/算力+电力协同.md  ← liquid-cooling frontmatter linked
├── wiki/concepts/2万亿算力基建计划.md ← liquid-cooling frontmatter linked
├── wiki/sources/2026-06-25-AI链更新-液冷-PCB.md  ← liquid-cooling 关键源(乐晴)
└── wiki/sources/2026-06-25-liquid-cooling-content-factory-summary.md  ← 反向登记
```