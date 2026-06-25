---
id: CON-20260625-003
type: 概念单元
title: Serenity 式 AI 算力产业链 8 层级拆解
source_documents:
  - SRC-WX-002
source_authors:
  - chenlei
themes:
  - AI算力
  - Serenity
  - 8层级
keywords:
  - 8层级
  - 下游到上游
  - 壁垒
  - 卡点定位
status: 已核对
canonical: true
version: 1
created_at: 2026-06-25
updated_at: 2026-06-25
definition: AI 算力产业链按下游到上游拆 8 层级: L1 下游需求 → L2 系统集成 → L3 GPU/AI 芯片 → L4 服务器/PC → L5 HBM/存储 → L6 制造/封测 → L7 稀土/铜铝(卡点) → L8 电力(卡点)
definition_context: 适用于 AI 算力产业链的卡点定位分析
conditions_of_validity: 适用于 2025-2026 H1 全球 AI 算力供应链
relationships:
  - target: QST-20260625-002
    type: 解释
  - target: OPI-20260625-002
    type: 解释
  - target: CAS-20260625-006
    type: 解释
  - target: CAS-20260625-007
    type: 解释
  - target: CAS-20260625-008
    type: 解释
---

## 核心内容

**Serenity 8 层级**(下游 → 上游):

| 层级 | 内容 | 扩产难度 | 卡点定位 |
|---|---|---|---|
| **L1** 下游需求 | AI 应用 / 算力中心 | 0.XX | 需求驱动 |
| **L2** 系统集成 | 服务器 / 整机厂 | 0.XX | 集成壁垒低 |
| **L3** AI 芯片 | GPU / 昇腾 / 寒武纪 | 0.XX | 显性瓶颈 |
| **L4** 服务器/PC | OEM / ODM | 0.XX | 制造壁垒中 |
| **L5** HBM/存储 | SK 海力士 / 美光 | 0.XX | 技术壁垒高 |
| **L6** 制造/封测 | 台积电 / 中芯国际 | 0.XX | 资本开支大 |
| **L7** 稀土/铜铝 | 北方稀土 / 紫金矿业 | 0.XX | **◆ 卡点 1+2** |
| **L8** 电力 | 长江电力 / 国家电网 | 0.XX | **◆ 1 号瓶颈** |

**核心判断**:真正的卡点在 **L7-L8**(资源端),不在 **L3**(GPU)。

## 来源依据

- morgan-ai-supply-chain.md 第 3 章(Serenity 8 层级细化版)
- 模板来源:templates/post-template-v2.md

[🟡 L2 · Serenity 方法论 + 大摩研报]

## 使用场景

- 任何 AI 算力卡点分析的章节
- 教学:Serenity 8 层级的实操案例
- 与 ai-gpu-power-mlcc(AI GPU 3 个新卡点)的对比框架

## 关联单元

- [[QST-20260625-002]]:主问题
- [[OPI-20260625-002]]:资源端观点
- [[CAS-20260625-006]]:L8 电力案例
- [[CAS-20260625-007]]:L7 稀土案例
- [[CAS-20260625-008]]:L7 铜铝案例

## 备注

- 与 ai-gpu-power-mlcc.md 的"3 个新卡点"形成对比:本篇强调资源端(L7-L8),E 篇强调 AI 算力下半场(国产替代/HBM/光模块)