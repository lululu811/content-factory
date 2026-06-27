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


# 内置公司名简称/全称/改名映射(避免 2024-2026 改名后白名单匹配不上)
# key=文中出现的名字,value=白名单里的官方名
NAME_ALIASES = {
    "博创科技": "长芯博创",     # 2024/12/17 更名
    "海康威视": "海康威视",     # 全称
    "中际旭创": "中际旭创",     # 简称
}


def normalize_company_name(name: str) -> str:
    """公司名归一化(简称/全称/改名映射)"""
    return NAME_ALIASES.get(name, name)


def extract_companies(snippet: str, title: str, whitelist: set = None) -> set:
    """从标题/摘要中提取可能的公司名(粗略正则 - 需人工核实)

    如果提供 whitelist(A 股全名单 set),只保留白名单内的公司名,
    避免误匹配"一群热爱光通信"等描述性短语。
    """
    # 匹配 2-6 字中文 + 常见公司名后缀(覆盖 X公司/X股份/X科/X学/X材/X料/X创/X智/X能/X达/X通/X技/X子 等)
    pattern = re.compile(r"([\u4e00-\u9fa5]{2,6}(?:公司|股份|集团|光电|科技|技术|电子|通信|激光|新材|半导体|高科|光学|材料|科创|智能|能源|智造|精机|精工|装备|创|智|能|达|通|技|子|网|芯|集成|德|新|特|微|信|动|力|生|源|合|成|品|业))")
    text = f"{title} {snippet}"
    companies = set()
    for m in pattern.finditer(text):
        c = m.group(1)
        if 3 <= len(c) <= 8:
            normalized = normalize_company_name(c)
            if whitelist is None or c in whitelist or normalized in whitelist:
                companies.add(normalized if normalized in (whitelist or set()) else c)
    return companies


DEFAULT_WHITELIST_CACHE = Path.home() / ".cache" / "a-stock-names.json"


def load_whitelist(path: Path = None) -> set:
    """加载 A 股公司名白名单(用于过滤 industry-kol-scan 误匹配)

    首次运行:
      mavis mcp call myMCP stock_basic '{}' > ~/.cache/a-stock-names.json
    或
      python3 scripts/industry-kol-scan.py --setup-whitelist
    """
    p = path or DEFAULT_WHITELIST_CACHE
    if not p.exists():
        return set()
    try:
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
        # 支持两种格式:[{name: ..., ts_code: ...}] 或直接 ["公司A", ...]
        if isinstance(data, list) and data and isinstance(data[0], dict):
            return {item.get("name") or item.get("ts_code") for item in data if item.get("name") or item.get("ts_code")}
        if isinstance(data, list):
            return set(data)
        return set()
    except (json.JSONDecodeError, KeyError, TypeError):
        return set()


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


def process_results(results: list, topic: str, slug: str, output_dir: str, whitelist: set = None) -> dict:
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
        all_companies |= extract_companies(s["snippet"], s["title"], whitelist)

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
    parser.add_argument("--topic", help="行业主题(setup-whitelist 模式不需要)")
    parser.add_argument("--slug", help="文章 slug(setup-whitelist 模式不需要)")
    parser.add_argument("--output-dir", default="/Users/chenlei/content-factory/drafts/raw")
    parser.add_argument("--input", help="web_search 结果 JSON 文件路径(stdin 或 --input)")
    parser.add_argument("--whitelist", help=f"A 股公司名白名单文件路径(JSON list,默认 ~/.cache/a-stock-names.json)")
    parser.add_argument("--setup-whitelist", action="store_true", help="拉取 myMCP stock_basic 全 A 股名单生成白名单")
    parser.add_argument("--no-whitelist", action="store_true", help="禁用白名单过滤(回退到原始正则)")
    args = parser.parse_args()

    # setup-whitelist 模式:拉取 myMCP stock_basic 生成 cache 文件
    if args.setup_whitelist:
        import subprocess
        DEFAULT_WHITELIST_CACHE.parent.mkdir(parents=True, exist_ok=True)
        print(f"📡 拉取 myMCP stock_basic...")
        try:
            result = subprocess.run(
                ["mavis", "mcp", "call", "myMCP", "stock_basic", "{}"],
                capture_output=True, text=True, timeout=60
            )
            if result.returncode == 0:
                raw = json.loads(result.stdout)
                items = raw if isinstance(raw, list) else raw.get("data", raw.get("items", []))
                names = sorted({item.get("name", "") for item in items if item.get("name")})
                with open(DEFAULT_WHITELIST_CACHE, "w", encoding="utf-8") as f:
                    json.dump(names, f, ensure_ascii=False, indent=2)
                print(f"✅ 白名单已生成:{len(names)} 家公司 → {DEFAULT_WHITELIST_CACHE}")
                return
            else:
                print(f"❌ myMCP 调用失败:{result.stderr}")
                sys.exit(1)
        except Exception as e:
            print(f"❌ 拉取失败:{e}")
            print("   可以手动执行:")
            print("   mavis mcp call myMCP stock_basic '{}' > ~/.cache/a-stock-names.json")
            sys.exit(1)

    if not args.input:
        print("❌ 本脚本需要 --input 参数(JSON 文件,包含 web_search 结果数组)")
        print("   用法:")
        print("   1. 在 agent 中调 web_search 工具,保存结果到 JSON")
        print("   2. python3 scripts/industry-kol-scan.py --input results.json --topic 光通信 --slug glass-bridge-cpo")
        print()
        print("   可选:首次运行拉取白名单(过滤误匹配):")
        print("   python3 scripts/industry-kol-scan.py --setup-whitelist")
        sys.exit(1)

    # 加载白名单
    whitelist = None
    if not args.no_whitelist:
        wl_path = Path(args.whitelist) if args.whitelist else DEFAULT_WHITELIST_CACHE
        whitelist = load_whitelist(wl_path)
        if whitelist:
            print(f"✅ 白名单:{len(whitelist)} 家公司(过滤误匹配)")
        else:
            print(f"⚠️  白名单未生成,使用原始正则(可能误匹配)")
            print(f"   建议运行:python3 scripts/industry-kol-scan.py --setup-whitelist")

    with open(args.input, encoding="utf-8") as f:
        results = json.load(f)
    if isinstance(results, dict) and "results" in results:
        results = results["results"]

    print(f"📥 读取 {len(results)} 条搜索结果")
    summary = process_results(results, args.topic, args.slug, args.output_dir, whitelist=whitelist)
    print(f"✅ 处理完成")
    print(f"   权威源:{summary['total_sources']} 个")
    print(f"   候选公司:{len(summary['mentioned_companies'])} 个(白名单过滤后)")
    print(f"   Markdown:{summary['markdown']}")
    print(f"   JSON:{summary['json']}")


if __name__ == "__main__":
    main()