#!/usr/bin/env bash
# research-reports-query.sh
# 在 ~/003_knowledge/knowledge_base/research-reports/ 里检索匹配的概念 + 飞书日报 source
# 用法: bash scripts/research-reports-query.sh "电力 算力 数据中心"
# 输出: top 15 匹配的 wiki 页面路径 + 标题 + 标签

set -euo pipefail

RESEARCH_DIR="${RESEARCH_DIR:-$HOME/003_knowledge/knowledge_base/research-reports}"
QUERY="${1:-}"
TOP_N="${TOP_N:-15}"

if [ -z "$QUERY" ]; then
    echo "用法: $0 <主题关键词,空格分隔> [top_n=15]"
    echo ""
    echo "示例:"
    echo "  $0 \"电力 算力 数据中心\""
    echo "  $0 \"稀土 永磁 出口管制\""
    echo "  $0 \"减速器 传感器 人形机器人\""
    exit 1
fi

if [ ! -d "$RESEARCH_DIR" ]; then
    echo "错误: $RESEARCH_DIR 不存在"
    exit 1
fi

# 用 Python 做精确的 frontmatter 解析 + 评分
python3 - "$RESEARCH_DIR" "$QUERY" "$TOP_N" <<'PYEOF'
import os
import re
import sys

research_dir = sys.argv[1]
query = sys.argv[2]
top_n = int(sys.argv[3])

# 关键词(空格分隔)
keywords = [k.strip() for k in query.split() if k.strip()]
if not keywords:
    sys.exit(0)

# 扫的目录
search_dirs = [
    ("wiki/concepts", "concept"),
    ("wiki/sources", "source"),
    ("wiki/entities", "entity"),
    ("wiki/syntheses", "synthesis"),
    ("wiki/mocs", "moc"),
]

def parse_frontmatter(content):
    """简单解析 YAML frontmatter"""
    if not content.startswith("---"):
        return {}
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}
    fm_text = parts[1]
    result = {}
    for line in fm_text.split("\n"):
        if ":" in line and not line.startswith(" "):
            k, v = line.split(":", 1)
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            if k in ("title", "type", "tags", "aliases", "source_type", "credibility"):
                if k == "tags" or k == "aliases":
                    v = re.findall(r"[\u4e00-\u9fff\w]+", v)
                result[k] = v
    return result

def score_doc(fm, content, keywords):
    """给文档打分(关键词在 title + tags + aliases + content 中出现次数)"""
    score = 0
    matched_keywords = set()
    fields = {
        "title": str(fm.get("title", "")),
        "tags": " ".join(fm.get("tags", [])),
        "aliases": " ".join(fm.get("aliases", [])),
        "type": str(fm.get("type", "")),
    }
    for kw in keywords:
        for field_name, field_val in fields.items():
            if kw in field_val:
                # title 权重最高,tags 中,正文低
                if field_name == "title":
                    score += 10
                elif field_name == "tags":
                    score += 5
                elif field_name == "aliases":
                    score += 4
                else:
                    score += 2
                matched_keywords.add(kw)
    # 正文匹配(低权重,只看一次)
    if any(kw in content for kw in keywords):
        score += 1
    return score, matched_keywords

results = []
for subdir, doc_type in search_dirs:
    full_dir = os.path.join(research_dir, subdir)
    if not os.path.exists(full_dir):
        continue
    for fname in os.listdir(full_dir):
        if not fname.endswith(".md"):
            continue
        fpath = os.path.join(full_dir, fname)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            continue
        fm = parse_frontmatter(content)
        if not fm:
            continue
        score, matched = score_doc(fm, content, keywords)
        if score > 0:
            results.append({
                "score": score,
                "matched": list(matched),
                "title": fm.get("title", fname[:-3]),
                "type": fm.get("type", doc_type),
                "path": f"{subdir}/{fname}",
                "tags": fm.get("tags", []),
            })

# 按分数排序
results.sort(key=lambda x: -x["score"])
results = results[:top_n]

# 输出
print(f"\n🔍 research-reports /query · 关键词: {' / '.join(keywords)}")
print(f"📊 命中 {len(results)} 个(查询 {sum(1 for _ in os.listdir(research_dir + '/wiki/concepts') if _.endswith('.md'))} 概念 + {sum(1 for _ in os.listdir(research_dir + '/wiki/sources') if _.endswith('.md'))} source)\n")

if not results:
    print("⚠️  未找到匹配。降级路径:")
    print("  1. 用更宽的关键词(如 'AI' / '数据' / '新能源')")
    print("  2. 直接读 wiki/index.md 浏览所有概念")
    print("  3. 跳过 research-reports 查证,只跑 serenity-skill + web_search\n")
else:
    for i, r in enumerate(results, 1):
        print(f"{i:>2}. [{r['score']:>3}分] {r['title']}")
        print(f"     路径: {r['path']}")
        print(f"     类型: {r['type']} · 匹配关键词: {', '.join(r['matched'])}")
        if r['tags']:
            tags_str = ' · '.join(r['tags'][:5])
            print(f"     标签: {tags_str}")
        print()

print("💡 下一步:")
print("  - 用 Read 工具读 top 5-10 概念全文")
print("  - 提取关键数据/公司/观点,写进文章正文")
print("  - 把命中的概念路径填到 frontmatter research_reports.linked_concepts")
PYEOF