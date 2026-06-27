#!/usr/bin/env python3
"""
content-factory Step 3 · 行业情报扫描工具(防漏标防御) v2

用法:
  python3 scripts/industry-kol-scan.py --topic "光通信" --slug glass-bridge-cpo
  python3 scripts/industry-kol-scan.py --topic "玻璃基板" --slug glass-substrate

输出:
  drafts/raw/<slug>/00-kol-scan.md
  drafts/raw/<slug>/00-kol-scan.json

注意:本脚本调用原生 web_search 工具(由 agent 在 Bash 中嵌入),
不通过 MCP matrix CLI(已弃用)。
"""
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path


# 注意:此脚本不能直接被 Python 解释器独立调用 web_search(MCP CLI 弃用)。
# 实际使用方式:
# 1. 在 agent 中调用 web_search 工具(原生工具,可用)
# 2. 把结果作为 --input 传入本脚本,或本脚本接收 stdin 输入
#
# 用法示例:
#   python3 scripts/industry-kol-scan.py --topic "光通信" --slug glass-bridge-cpo --input results.json


INTL_AUTHORITY = ["Omdia", "Yole", "TrendForce", "Prismark", "LightCounting", "IDC", "Gartner", "Counterpoint", "SemiAnalysis"]
BROKER_REPORT = ["证券", "研报", "深度报告", "分析师", "首席", "策略", "行业点评"]
GENERAL_FINANCE = ["财经", "新闻", "经济报道", "见闻", "观察报", "新浪财经", "东方财富", "同花顺", "华尔街", "证券时报"]
VERTICAL_MEDIA = ["公众号", "微信", "头条", "订阅", "CINNO", "讯石", "OFweek", "光纤在线", "通信人家园", "半导体行业观察", "芯智讯"]


def classify_source(title: str, snippet: str, source: str) -> tuple:
    text = f"{title} {snippet} {source}"
    if any(k in text for k in INTL_AUTHORITY):
        return "国际权威数据", "🟢"
    if any(k in text for k in BROKER_REPORT):
        return "券商研报", "🟡"
    if any(k in text for k in GENERAL_FINANCE):
        return "通用财经媒体", "🟡"
    return "专业垂直媒体", "🟢"


def extract_companies(snippet: str, title: str) -> set:
    """从标题/摘要中提取可能的公司名(粗略正则 - 需人工核实)"""
    pattern = re.compile(r"([\u4e00-\u9fa5]{2,6}(?:公司|股份|集团|光电|科技|技术|电子|通信|激光|新材|半导体))")
    text = f"{title} {snippet}"
    companies = set()
    for m in pattern.finditer(text):
        c = m.group(1)
        if 3 <= len(c) <= 8:
            companies.add(c)
    return companies


def generate_keywords(topic: str) -> list:
    return [
        f"{topic} 公众号",
        f"{topic} 大V",
        f"{topic} 博主",
        f"{topic} 媒体",
        f"{topic} 首席分析师",
        f"{topic} 深度报告",
        f"{topic} 产业链",
        f"{topic} KOL",
    ]


def process_results(results: list, topic: str, slug: str, output_dir: str) -> dict:
    """处理 web_search 结果,生成 markdown + json 报告"""
    sources = {}

    for r in results:
        key = (r.get("title", ""), r.get("link", ""))
        if key not in sources:
            cat, quality = classify_source(
                r.get("title", ""), r.get("snippet", ""), r.get("source", "")
            )
            sources[key] = {
                "title": r.get("title", ""),
                "snippet": r.get("snippet", ""),
                "source": r.get("source", ""),
                "link": r.get("link", ""),
                "category": cat,
                "quality": quality,
            }

    # 提取公司
    all_companies = set()
    for s in sources.values():
        all_companies |= extract_companies(s["snippet"], s["title"])

    # 分类
    by_category = {}
    for s in sources.values():
        by_category.setdefault(s["category"], []).append(s)

    # 输出 markdown
    output_dir_path = Path(output_dir) / slug
    output_dir_path.mkdir(parents=True, exist_ok=True)

    md = f"# {topic} 行业 KOL/公众号情报扫描\n\n"
    md += f"> **扫描时间**:{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    md += f"> **扫描工具**:`scripts/industry-kol-scan.py`(web_search 原生工具)\n"
    md += f"> **主题**:`{topic}`\n"
    md += f"> **覆盖范围**:专业垂直 / 通用财经 / 国际数据 / 券商研报\n\n"

    md += "## 一、权威源汇总\n\n"
    md += f"共 **{len(sources)}** 个权威源(去重后)\n\n"

    cat_order = [
        ("专业垂直媒体", "🟢"),
        ("通用财经媒体", "🟡"),
        ("国际权威数据", "🟢"),
        ("券商研报", "🟡"),
    ]
    for cat, icon in cat_order:
        if cat not in by_category:
            continue
        md += f"### {cat}({icon})\n\n"
        md += "| 标题 | 来源 | 关键内容 |\n"
        md += "|---|---|---|\n"
        for s in by_category[cat][:15]:
            title_short = s["title"][:55].replace("|", "/").replace("\n", " ")
            src_short = (s["source"] or "?")[:25]
            snippet = s["snippet"][:100].replace("|", "/").replace("\n", " ")
            md += f"| {title_short} | {src_short} | {snippet} |\n"
        md += "\n"

    md += "## 二、漏标的交叉验证清单\n\n"
    md += f"> 自动从扫描结果中提取 **{len(all_companies)}** 个候选公司(需人工核实)\n\n"
    md += "| 候选公司 | 是否已列入文章 | 决定 |\n"
    md += "|---|---|---|\n"
    for c in sorted(all_companies):
        md += f"| {c} | 待核实 | 待 Phase 4 数据拉取后决定 |\n"
    md += "\n"

    md += "## 三、数据来源标注规范\n\n"
    md += "后续正文每个数据点必须标注:**来源 + 质量 + 快照日期**\n\n"
    md += "**示例**:\n\n"
    md += "```markdown\n"
    md += "- 汇成真空 6/26 收盘 ¥243.80(数据快照 6/26,数据源 CINNO Research + 巨潮)\n"
    md += "- Omdia 2026 玻璃基板 186 亿美元(Omdia 2026 报告,🟢)\n"
    md += "- 中际旭创 1.6T 全球市占 33%(讯石光通讯网 2026 行业分析,🟢)\n"
    md += "```\n\n"

    md += "## 四、本文涉及公司清单(完整版 · Phase 4 后填写)\n\n"
    md += "| # | 公司 | ts_code | 来源(扫描结果) |\n"
    md += "|---|---|---|---|\n"
    md += "| | | | |\n"

    out_md = output_dir_path / "00-kol-scan.md"
    with open(out_md, "w", encoding="utf-8") as f:
        f.write(md)

    out_json = output_dir_path / "00-kol-scan.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump({
            "topic": topic,
            "slug": slug,
            "scanned_at": datetime.now().isoformat(),
            "total_sources": len(sources),
            "mentioned_companies": sorted(all_companies),
            "sources": list(sources.values()),
        }, f, ensure_ascii=False, indent=2)

    return {
        "total_sources": len(sources),
        "mentioned_companies": sorted(all_companies),
        "markdown": str(out_md),
        "json": str(out_json),
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="content-factory Step 3 · 行业情报扫描工具")
    parser.add_argument("--topic", required=True, help="行业主题")
    parser.add_argument("--slug", required=True, help="文章 slug")
    parser.add_argument("--output-dir", default="/Users/chenlei/content-factory/drafts/raw")
    parser.add_argument("--input", help="web_search 结果 JSON 文件路径(stdin 或 --input)")
    args = parser.parse_args()

    if not args.input:
        print("❌ 本脚本需要 --input 参数(JSON 文件,包含 web_search 结果数组)")
        print("   用法:")
        print("   1. 在 agent 中调 web_search 工具,保存结果到 JSON")
        print("   2. python3 scripts/industry-kol-scan.py --input results.json --topic 光通信 --slug glass-bridge-cpo")
        sys.exit(1)

    with open(args.input, encoding="utf-8") as f:
        results = json.load(f)
    if isinstance(results, dict) and "results" in results:
        results = results["results"]

    print(f"📥 读取 {len(results)} 条搜索结果")
    summary = process_results(results, args.topic, args.slug, args.output_dir)
    print(f"✅ 处理完成")
    print(f"   权威源:{summary['total_sources']} 个")
    print(f"   候选公司:{len(summary['mentioned_companies'])} 个")
    print(f"   Markdown:{summary['markdown']}")
    print(f"   JSON:{summary['json']}")


if __name__ == "__main__":
    main()