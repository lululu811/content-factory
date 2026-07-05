#!/usr/bin/env python3
"""
巨潮资讯网公告查询工具 — 通用工具类

输入:股票代码列表(命令行 / 文件 / stdin)
输出:公告元数据 JSON / Markdown 摘要(到 stdout 或文件)

设计原则:
  - **工具类**:不绑定任何特定项目 / 主题 / 文件布局
  - 输入灵活:支持单家 / 多个命令行 / 文件 / stdin
  - 输出灵活:JSON 或 Markdown 摘要,stdout 或 --output 文件
  - 限速 0.5s/家避免巨潮 IP 封禁
  - 完全免费,绕过 myMCP anns_d 40203 付费墙

用法:
  # 单家
  python3 cninfo-anns.py 600487.SH --days 14

  # 多家(命令行)
  python3 cninfo-anns.py 600487.SH 600498.SH 300308.SZ --days 14 --json

  # 从文件读代码列表(每行一个 / 逗号分隔)
  python3 cninfo-anns.py --code-file codes.txt --days 14 --json --output anns.json

  # 从 stdin 读
  cat codes.txt | python3 cninfo-anns.py --code-stdin --days 14 --json

  # Markdown 摘要(打印到 stdout)
  python3 cninfo-anns.py 600487.SH 600498.SH --days 30

依赖:仅 Python 标准库,无第三方包
"""
import argparse
import json
import re
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional


# 巨潮官方 API
CNINFO_API = "http://www.cninfo.com.cn/new/hisAnnouncement/query"
# szse_stock.json 实际包含全部 A 股(沪深主板+创业板+科创板+北交所)
CNINFO_STOCK_LIST_ALL = "http://www.cninfo.com.cn/new/data/szse_stock.json"


def curl_post(url: str, data: dict, retries: int = 3) -> Optional[dict]:
    """POST 巨潮 API"""
    import urllib.parse
    encoded = urllib.parse.urlencode(data)
    for i in range(retries):
        try:
            r = subprocess.run(
                ["curl", "-s", "-X", "POST", url,
                 "-H", "Content-Type: application/x-www-form-urlencoded",
                 "-H", "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                 "-H", "Accept: */*",
                 "-H", "Referer: http://www.cninfo.com.cn/new/commonUrl?url=disclosure/list/notice",
                 "--data", encoded],
                capture_output=True, text=True, timeout=30,
            )
            if r.returncode == 0 and r.stdout.strip():
                return json.loads(r.stdout)
        except Exception as e:
            if i == retries - 1:
                print(f"  ERROR: {e}", file=sys.stderr)
        time.sleep(1)
    return None


def get_org_id(ts_code: str) -> Optional[str]:
    """获取股票代码对应的 orgId(szse_stock.json 实际包含全部 A 股)"""
    code = ts_code.split(".")[0]
    try:
        r = subprocess.run(
            ["curl", "-s", CNINFO_STOCK_LIST_ALL, "-H", "User-Agent: Mozilla/5.0"],
            capture_output=True, text=True, timeout=30,
        )
        if r.returncode == 0:
            data = json.loads(r.stdout)
            for s in data.get("stockList", []):
                if s.get("code") == code:
                    return s.get("orgId")
    except Exception:
        pass
    return None


def get_announcements(ts_code: str, start_date: str, end_date: str,
                      page_size: int = 30, plate: Optional[str] = None) -> List[Dict]:
    """
    查询指定公司公告
    start_date / end_date: YYYY-MM-DD
    """
    code = ts_code.split(".")[0]
    if plate is None:
        if code.startswith("6"):
            plate = "sse"
        elif code.startswith("8") or code.startswith("4") or code.startswith("9"):
            plate = "bj"
        else:
            plate = "szse"

    org_id = get_org_id(ts_code)
    if not org_id:
        print(f"  ⚠️  {ts_code} 找不到 orgId", file=sys.stderr)
        return []

    data = curl_post(CNINFO_API, {
        "stock": f"{code},{org_id}",
        "tabName": "fulltext",
        "pageSize": page_size,
        "pageNum": 1,
        "column": plate,
        "category": "",
        "seDate": f"{start_date}~{end_date}",
        "isHLtitle": "true",
    })
    if not data:
        return []
    results = []
    for a in (data.get("announcements") or []):
        ts_ms = a.get("announcementTime", 0)
        ann_date = datetime.fromtimestamp(ts_ms / 1000).strftime("%Y-%m-%d")
        adj_url = a.get("adjunctUrl", "")
        results.append({
            "ann_id": a.get("announcementId"),
            "ts_code": ts_code,
            "org_id": org_id,
            "ann_date": ann_date,
            "title": a.get("announcementTitle", "").strip(),
            "url": "http://static.cninfo.com.cn/" + adj_url if adj_url else "",
            "sec_code": a.get("secCode", code),
        })
    return results


def batch_query(ts_codes: List[str], days: int = 14) -> Dict[str, List[Dict]]:
    """批量查询多家公司"""
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    all_results = {}
    for i, ts in enumerate(ts_codes, 1):
        print(f"[{i}/{len(ts_codes)}] {ts} ...", file=sys.stderr, end=" ")
        results = get_announcements(ts, start_date, end_date)
        all_results[ts] = results
        print(f"{len(results)} 条", file=sys.stderr)
        time.sleep(0.5)  # 限速
    return all_results


def parse_code_list_from_file(path: Path) -> List[str]:
    """从文件读代码列表(支持每行一个 / 逗号分隔 / 空格分隔)"""
    text = path.read_text(encoding="utf-8")
    # 支持多种分隔:换行 / 逗号 / 空格 / tab
    raw_codes = re.split(r'[\s,;]+', text)
    return [c.strip() for c in raw_codes if c.strip() and re.match(r'^\d{6}\.[A-Z]{2}$', c.strip())]


def format_markdown_summary(results: Dict[str, List[Dict]], title: str = "") -> str:
    """生成 Markdown 格式摘要字符串(返回,不打印)"""
    total = sum(len(v) for v in results.values())
    lines = [f"\n## {title or '公告摘要'}({len(results)} 家公司 · {total} 条公告)\n"]
    for ts, anns in results.items():
        if not anns:
            lines.append(f"### {ts} — 0 条\n")
            continue
        lines.append(f"### {ts} — {len(anns)} 条")
        for a in anns[:10]:
            lines.append(f"- [{a['ann_date']}] {a['title'][:80]}")
            lines.append(f"  - {a['url']}")
        if len(anns) > 10:
            lines.append(f"- ... +{len(anns)-10} more")
        lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="巨潮资讯网公告查询工具(通用,免费)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("ts_codes", nargs="*",
                        help="股票代码列表(空格分隔,如:600487.SH 300308.SZ)")
    parser.add_argument("--code-file",
                        help="从文件读代码列表(每行一个 / 逗号分隔)")
    parser.add_argument("--code-stdin", action="store_true",
                        help="从 stdin 读代码列表")
    parser.add_argument("--days", type=int, default=14,
                        help="查询最近 N 天(默认 14)")
    parser.add_argument("--start", help="开始日期 YYYY-MM-DD(覆盖 --days)")
    parser.add_argument("--end", help="结束日期 YYYY-MM-DD(默认今天)")
    parser.add_argument("--json", action="store_true",
                        help="输出 JSON 格式")
    parser.add_argument("--output", "-o",
                        help="输出文件路径(默认 stdout)")
    args = parser.parse_args()

    # 收集 ts_codes
    codes: List[str] = list(args.ts_codes)
    if args.code_file:
        codes.extend(parse_code_list_from_file(Path(args.code_file)))
    if args.code_stdin:
        stdin_text = sys.stdin.read()
        for c in re.split(r'[\s,;]+', stdin_text):
            c = c.strip()
            if c and re.match(r'^\d{6}\.[A-Z]{2}$', c):
                codes.append(c)

    if not codes:
        print("❌ 必须提供股票代码(命令行 / --code-file / --code-stdin)")
        parser.print_help()
        sys.exit(1)

    # 去重保序
    seen = set()
    codes = [c for c in codes if not (c in seen or seen.add(c))]

    print(f"📋 待查询:{len(codes)} 家公司 / 最近 {args.days} 天", file=sys.stderr)

    # 查询
    if len(codes) == 1:
        end_date = args.end or datetime.now().strftime("%Y-%m-%d")
        start_date = args.start or (datetime.now() - timedelta(days=args.days)).strftime("%Y-%m-%d")
        results_list = get_announcements(codes[0], start_date, end_date)
        results = {codes[0]: results_list}
    else:
        results = batch_query(codes, args.days)

    # 输出
    if args.json:
        output_text = json.dumps(results, ensure_ascii=False, indent=2)
    else:
        output_text = format_markdown_summary(results, title=f"巨潮公告摘要({args.days} 天)")

    if args.output:
        Path(args.output).write_text(output_text, encoding="utf-8")
        print(f"✅ 已写入:{args.output}({len(output_text)} 字符)", file=sys.stderr)
    else:
        print(output_text)


if __name__ == "__main__":
    main()