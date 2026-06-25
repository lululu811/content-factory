#!/usr/bin/env python3
"""批量给 dbs-content-system 单元加 research_reports 反向链接

策略:从单元的 keywords + themes 提取关键词,在 research-reports wiki/concepts/ 里找匹配。
"""
import os
import re
import yaml
from pathlib import Path

UNIT_BASE = Path("/Users/chenlei/content-factory/02-内容单元库")
RESEARCH_DIR = Path.home() / "003_knowledge/knowledge_base/research-reports"
CONCEPTS_DIR = RESEARCH_DIR / "wiki/concepts"
SOURCES_DIR = RESEARCH_DIR / "wiki/sources"


def load_concept_index():
    """预加载所有 research-reports 概念的 frontmatter(title + tags + aliases)"""
    index = []
    for f in CONCEPTS_DIR.glob("*.md"):
        try:
            content = f.read_text(encoding="utf-8")
        except Exception:
            continue
        # 简单 frontmatter 解析
        if not content.startswith("---"):
            continue
        parts = content.split("---", 2)
        if len(parts) < 3:
            continue
        fm_text = parts[1]
        fm = {}
        for line in fm_text.split("\n"):
            if ":" in line and not line.startswith(" "):
                k, _, v = line.partition(":")
                fm[k.strip()] = v.strip().strip('"').strip("'")
        if "title" in fm:
            index.append({
                "title": fm["title"],
                "tags": fm.get("tags", ""),
                "aliases": fm.get("aliases", ""),
                "path": f"wiki/concepts/{f.name}",
            })
    return index


def match_concepts(unit_keywords, unit_themes, concepts_index, top_n=3):
    """根据单元的 keywords + themes 找 top N 匹配 research-reports 概念"""
    # 过滤掉非字符串元素(如 int / float / None)
    keywords = []
    for k in (unit_keywords or []):
        if isinstance(k, str):
            keywords.append(k)
    for t in (unit_themes or []):
        if isinstance(t, str):
            keywords.append(t)

    # 关键词转小写以便匹配
    keywords_lower = {k.lower() for k in keywords if k}

    scored = []
    for c in concepts_index:
        score = 0
        title_lower = c["title"].lower()
        tags_lower = (c["tags"] or "").lower()
        aliases_lower = (c["aliases"] or "").lower()
        for kw in keywords_lower:
            if kw in title_lower:
                score += 10
            elif kw in tags_lower:
                score += 5
            elif kw in aliases_lower:
                score += 4
        if score > 0:
            scored.append((score, c))
    scored.sort(key=lambda x: -x[0])
    return [c for _, c in scored[:top_n]]


def process_unit(unit_path, concepts_index):
    """给单个单元加 research_reports 反向链接"""
    content = unit_path.read_text(encoding="utf-8")

    if "research_reports:" in content[:1500]:
        # 已加,跳过
        return False

    # 解析 frontmatter
    if not content.startswith("---"):
        return False
    parts = content.split("---", 2)
    if len(parts) < 3:
        return False
    fm_text = parts[1]
    fm = {}
    try:
        fm = yaml.safe_load(fm_text) or {}
    except Exception:
        # 手动解析
        for line in fm_text.split("\n"):
            if ":" in line and not line.startswith(" "):
                k, _, v = line.partition(":")
                fm[k.strip()] = v.strip().strip('"').strip("'")

    keywords = fm.get("keywords", [])
    themes = fm.get("themes", [])
    if isinstance(keywords, str):
        keywords = [k.strip() for k in keywords.strip("[]").split(",")]
    if isinstance(themes, str):
        themes = [t.strip() for t in themes.strip("[]").split(",")]

    matched = match_concepts(keywords, themes, concepts_index, top_n=3)
    if not matched:
        return False

    # 生成 research_reports 反向链接段
    lines = ["", "research_reports:", "  reverse_linked: true"]
    lines.append(f"  matched_concepts: {len(matched)}")
    lines.append("  linked_concepts:")
    for c in matched:
        lines.append(f"    - name: \"{c['title']}\"")
        lines.append(f"      path: \"{c['path']}\"")
        lines.append(f"      match_score: \"keywords + themes 匹配\"")
    new_block = "\n".join(lines)

    # 在 frontmatter 末尾追加
    new_fm = fm_text.rstrip() + "\n" + new_block.lstrip() + "\n"
    new_content = content[:len(parts[0]) + 2] + new_fm + "---" + content[len(parts[0]) + 2 + len(fm_text) + 4:]
    unit_path.write_text(new_content, encoding="utf-8")
    return True


def main():
    concepts_index = load_concept_index()
    print(f"📚 加载 research-reports 概念索引: {len(concepts_index)} 个")

    processed = 0
    skipped = 0
    failed = 0
    for sub in ["问题单元", "观点单元", "概念单元", "案例单元", "方案单元"]:
        sub_dir = UNIT_BASE / sub
        if not sub_dir.exists():
            continue
        for f in sorted(sub_dir.glob("*.md")):
            try:
                if process_unit(f, concepts_index):
                    processed += 1
                else:
                    skipped += 1
            except Exception as e:
                print(f"❌ {f.name}: {e}")
                failed += 1

    print(f"\n✅ 新加 research_reports 链接: {processed}")
    print(f"⏭️  跳过(已加或无匹配): {skipped}")
    print(f"❌ 处理失败: {failed}")


if __name__ == "__main__":
    main()