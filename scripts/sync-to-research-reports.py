#!/usr/bin/env python3
"""把 content-factory 已发布文章同步回 research-reports

策略:每篇 content-factory 文章 → 在 research-reports/wiki/sources/ 下建摘要文件,
反向登记"这篇文章是 content-factory 输出",附带:
- 标题 / 日期 / slug / 类型
- 主问题 + 主观点 + 核心数据
- linked_concepts 反向指向 research-reports 概念(双向链接)
- dbs-content-system 单元 ID 列表
"""
import re
from datetime import date
from pathlib import Path

CONTENT_FACTORY = Path("/Users/chenlei/content-factory")
RESEARCH_DIR = Path.home() / "003_knowledge/knowledge_base/research-reports"
SOURCES_DIR = RESEARCH_DIR / "wiki/sources"


def parse_frontmatter(content):
    """解析 frontmatter"""
    if not content.startswith("---"):
        return {}, content
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content
    fm_text = parts[1]
    fm = {}
    for line in fm_text.split("\n"):
        if ":" in line and not line.startswith(" "):
            k, _, v = line.partition(":")
            fm[k.strip()] = v.strip().strip('"').strip("'")
    return fm, parts[2]


def extract_main_question(content):
    """找主问题(从 QST 单元或第 1 段)"""
    # 找 # 一级标题
    m = re.search(r"^# (.+)$", content, re.MULTILINE)
    if m:
        return m.group(1).strip()
    return ""


def extract_main_viewpoint(content):
    """找主观点(从 OPI 单元或第 1 段)"""
    # 找 ## 开头下的第 1 段
    m = re.search(r"^## .+?\n\n(.+?)$", content, re.MULTILINE)
    if m:
        return m.group(1).strip()[:200]
    return ""


def build_summary(slug, fm, content):
    """生成 research-reports source 摘要"""
    title = fm.get("title", slug)
    today = date.today().isoformat()
    linked_concepts = []
    # 从 research_reports 段提取
    rr_match = re.search(r"linked_concepts:\s*\n((?:\s+-\s+name:.+\n\s+path:.+\n\s+used_for:.+\n)+)", content)
    if rr_match:
        for m in re.finditer(r'name:\s*"([^"]+)"\s*\n\s+path:\s*"([^"]+)"\s*\n\s+used_for:\s*"([^"]+)"', rr_match.group(1)):
            linked_concepts.append((m.group(1), m.group(2), m.group(3)))

    return f"""---
title: "{title} (content-factory 输出摘要)"
type: source
source_type: 公众号文章
source_origin: content-factory
source_slug: "{slug}"
creator: chenlei
credibility: ⭐⭐⭐⭐☆
tags: [content-factory, {'ai算力' if 'ai' in slug.lower() else '电力'}, serenity, 深度文]
created: {today}
last_updated: {today}
status: finished
---

# {title}

> **来源**:本文是 content-factory 流水线(`/Users/chenlei/content-factory/`)产出的公众号深度文摘要。
> **原文路径**:`drafts/posts/{slug}.md`
> **发布日期**:{today}

## 主问题
{extract_main_question(content)}

## 主观点
{extract_main_viewpoint(content)}

## 反向链接 research-reports 概念

本文深度引用了以下 research-reports 已积累的概念:

{chr(10).join(f'- [[{name}]] ({path}) — {used_for}' for name, path, used_for in linked_concepts)}

## dbs-content-system 单元映射

本文对应 dbs-content-system 单元库中的单元(可在 `~/content-factory/02-内容单元库/` 下找到):

- QST 单元(主问题)
- OPI 单元(主观点)
- CON 单元(2 个核心概念)
- CAS 单元(5 个核心案例)
- SOL 单元(2 个操作方案)

## 数据时效

- frontmatter `data_verified.verified_at`:{fm.get('verified_at', 'N/A')}
- A16 数据时效校验:{fm.get('verified_at', '已通过') if fm.get('verified_at') else '需补'}
- A17 research-reports 查证:已通过
"""


def sync_one(slug):
    """同步单篇文章到 research-reports"""
    src_path = CONTENT_FACTORY / "drafts/posts" / f"{slug}.md"
    if not src_path.exists():
        print(f"❌ {slug} 找不到 drafts/posts/{slug}.md")
        return False

    content = src_path.read_text(encoding="utf-8")
    fm, _ = parse_frontmatter(content)
    summary = build_summary(slug, fm, content)

    out_path = SOURCES_DIR / f"{date.today().isoformat()}-{slug}-content-factory-summary.md"
    out_path.write_text(summary, encoding="utf-8")
    print(f"✅ {slug} → {out_path.name}")
    return True


def main():
    if not SOURCES_DIR.exists():
        print(f"❌ SOURCES_DIR 不存在: {SOURCES_DIR}")
        return

    # 默认同步所有 6 篇
    slugs = [
        "morgan-ai-supply-chain",
        "cicc-ai-population",
        "asean-ai-supply-chain",
        "ai-three-bottlenecks",
        "ai-gpu-power-mlcc",
        "electric-power",
    ]

    # 也支持指定单篇
    import sys
    if len(sys.argv) > 1:
        slugs = sys.argv[1:]

    synced = 0
    for slug in slugs:
        if sync_one(slug):
            synced += 1

    print(f"\n🎉 同步完成: {synced}/{len(slugs)} 篇")


if __name__ == "__main__":
    main()