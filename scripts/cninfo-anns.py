#!/usr/bin/env python3
"""
巨潮资讯网公告查询工具(content-factory 备选数据源)

用法:
  # 单家公司最近 7 天公告
  python3 scripts/cninfo-anns.py --ts-code 603773.SH --days 7

  # 26 家批量
  python3 scripts/cninfo-anns.py --batch glass-bridge-cpo --days 14

  # 输出 JSON
  python3 scripts/cninfo-anns.py --ts-code 603773.SH --json
"""
import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional


CNINFO_API = "http://www.cninfo.com.cn/new/hisAnnouncement/query"
# 重要:szse_stock.json 实际包含所有 A 股(沪深主板+创业板+科创板+北交所)
# sse_stock.json 是 404,hke_stock.json 是港股
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
    # 判断交易所
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


def main():
    parser = argparse.ArgumentParser(description="巨潮资讯网公告查询工具")
    parser.add_argument("--ts-code", help="单家股票代码(600519.SH)")
    parser.add_argument("--days", type=int, default=14, help="查询最近 N 天")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    parser.add_argument("--batch", help="批量:玻璃基板公司列表文件 / 预定义集")
    args = parser.parse_args()

    # 预定义批量集
    BATCH_PRESETS = {
        "glass-bridge-cpo": [
            # 第 8 篇 14 家
            "603773.SH", "300776.SZ", "688603.SH", "000725.SZ",
            "301188.SZ", "688170.SH", "688559.SH", "600584.SH",
            "002156.SZ", "688700.SH", "002436.SZ", "600707.SH",
            "920438.BJ", "600552.SH",
            # 第 9 篇 12 家
            "300308.SZ", "300502.SZ", "300394.SZ", "688048.SH",
            "601869.SH", "002491.SZ", "688143.SH", "002384.SZ",
            "301205.SZ", "603938.SH", "300706.SZ", "603986.SH",
        ],
    }

    if args.ts_code:
        end = datetime.now().strftime("%Y-%m-%d")
        start = (datetime.now() - timedelta(days=args.days)).strftime("%Y-%m-%d")
        results = get_announcements(args.ts_code, start, end)
        if args.json:
            print(json.dumps(results, ensure_ascii=False, indent=2))
        else:
            print(f"\n=== {args.ts_code} 最近 {args.days} 天公告 ===")
            for r in results:
                print(f"  [{r['ann_date']}] {r['title']}")
                print(f"    {r['url']}")
    elif args.batch:
        codes = BATCH_PRESETS.get(args.batch)
        if not codes:
            print(f"未定义的批量集: {args.batch},可选: {list(BATCH_PRESETS.keys())}")
            sys.exit(1)
        results = batch_query(codes, args.days)
        # 输出
        if args.json:
            print(json.dumps(results, ensure_ascii=False, indent=2))
        else:
            print(f"\n=== {args.batch} {len(codes)} 家公司最近 {args.days} 天公告 ===\n")
            total = 0
            for ts, anns in results.items():
                if anns:
                    print(f"【{ts}】{len(anns)} 条")
                    for a in anns[:5]:
                        print(f"  [{a['ann_date']}] {a['title'][:60]}")
                    if len(anns) > 5:
                        print(f"  ... +{len(anns)-5} more")
                    total += len(anns)
                    print()
            print(f"📊 总计 {total} 条公告")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()