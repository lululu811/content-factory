#!/usr/bin/env python3
"""
scripts/bibi-status-report.py
bibigpt 现状报告（一次性脚本 · 基于 logs/bibi-calls.jsonl）

输出 markdown 报告到 stdout，6 个维度：
  1. 整体使用（调用次数 + 累计 cost_duration）
  2. 可用性统计（available true/false 比例）
  3. Hallucination 统计（summarize 命中率）
  4. 失败频道（当前 + 历史）
  5. 额度消耗（按天 + 按命令）
  6. 建议（哪些频道该取消、哪些字幕该手工补）

用法：
  python3 bibi-status-report.py
  python3 bibi-status-report.py --out /path/to/report.md
  python3 bibi-status-report.py --days 7
"""

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

LOG_DIR = Path.home() / "content-factory" / "logs"
CALLS_LOG = LOG_DIR / "bibi-calls.jsonl"
FAILED_LOG = LOG_DIR / "failed-channels.jsonl"


def load_calls(days: int = None):
    """加载 calls 日志，可选按天数过滤"""
    if not CALLS_LOG.exists():
        return []
    cutoff = (
        datetime.now(timezone.utc) - timedelta(days=days)
    ).isoformat() if days else None

    records = []
    with open(CALLS_LOG, encoding="utf-8") as f:
        for line in f:
            try:
                rec = json.loads(line)
                if cutoff and rec.get("called_at", "") < cutoff:
                    continue
                records.append(rec)
            except json.JSONDecodeError:
                continue
    return records


def load_failed_channels(days: int = None):
    """加载失败频道历史"""
    if not FAILED_LOG.exists():
        return []
    cutoff_date = (
        datetime.now().date() - timedelta(days=days)
    ).isoformat() if days else None

    records = []
    with open(FAILED_LOG, encoding="utf-8") as f:
        for line in f:
            try:
                rec = json.loads(line)
                if cutoff_date and rec.get("date", "") < cutoff_date:
                    continue
                records.append(rec)
            except json.JSONDecodeError:
                continue
    return records


def gen_report(days: int = None) -> str:
    calls = load_calls(days)
    failed = load_failed_channels(days)

    if not calls and not failed:
        return "⚠️  无 bibi 调用记录。请先运行 daily-feed.sh 或 bibi-safe.py"

    # ============ 1. 整体使用 ============
    by_cmd = Counter(r["command"] for r in calls)
    total_cost_sec = sum(r.get("cost_duration", 0) for r in calls)
    total_cost_min = total_cost_sec / 60

    # ============ 2. 可用性 ============
    gs_calls = [r for r in calls if r["command"] in ("get-subtitle", "summarize")]
    gs_available_true = sum(1 for r in gs_calls if r["available"])
    gs_available_false = len(gs_calls) - gs_available_true
    avail_rate = (gs_available_true / len(gs_calls) * 100) if gs_calls else 0

    # ============ 3. Hallucination ============
    sm_calls = [r for r in calls if r["command"] == "summarize"]
    sm_hallucination = sum(1 for r in sm_calls if r["is_hallucination"])
    halluc_rate = (sm_hallucination / len(sm_calls) * 100) if sm_calls else 0

    # 按 URL 统计 hallucination（哪些视频被 hallucination）
    halluc_urls = [
        (r["url"], r.get("reason", ""))
        for r in sm_calls if r["is_hallucination"]
    ]

    # ============ 4. 失败频道 ============
    failed_titles = set()
    failed_streaks = defaultdict(set)
    for rec in failed:
        for ch in rec.get("failed", []):
            failed_titles.add(ch["title"])
            failed_streaks[ch["title"]].add(rec["date"])

    streak_lines = []
    for title, dates in sorted(failed_streaks.items()):
        sorted_dates = sorted(dates)
        streak_lines.append((title, len(sorted_dates), sorted_dates))

    streak_lines.sort(key=lambda x: -x[1])

    # ============ 5. 额度消耗（按天）===========
    by_date = defaultdict(lambda: {"count": 0, "cost_sec": 0})
    for r in calls:
        date = r["called_at"][:10]
        by_date[date]["count"] += 1
        by_date[date]["cost_sec"] += r.get("cost_duration", 0)

    # ============ 6. 建议 ============
    suggestions = []

    # 6.1 连续失败频道
    streak_alerts = [
        (t, n, d) for t, n, d in streak_lines if n >= 3
    ]
    if streak_alerts:
        titles = ", ".join(f"`{t}`" for t, _, _ in streak_alerts)
        suggestions.append(
            f"🔴 **连续失败频道** ({len(streak_alerts)} 个)：{titles} —— "
            f"建议在 bibi 后台取消订阅或换 RSSHub 抓取"
        )

    # 6.2 Hallucination 比例
    if halluc_rate >= 50 and sm_calls:
        suggestions.append(
            f"⚠️  **Hallucination 高发** ({halluc_rate:.0f}%): {sm_hallucination}/{len(sm_calls)} 次 summarize "
            f"返回 LLM 编造内容 —— 建议所有 summarize 调用都走 bibi-safe.py 检查"
        )

    # 6.3 get-subtitle 可用性低
    if gs_calls and avail_rate < 50:
        suggestions.append(
            f"⚠️  **get-subtitle 可用性低** ({avail_rate:.0f}%): {gs_available_false}/{len(gs_calls)} 次返回空字幕 —— "
            f"建议加 playwright/yt-dlp 备用字幕抓取方案"
        )

    # 6.4 累计扣费多
    if total_cost_min >= 30:
        suggestions.append(
            f"💰 **累计扣费**: {total_cost_min:.1f} 分钟（pro 100 分钟/月）—— "
            f"建议改用 `get-subtitle` 拿真实字幕，避免 summarize 编造"
        )

    if not suggestions:
        suggestions.append("✅ **状态正常**，无明显需要调整的地方")

    # ============ 输出 markdown ============
    days_label = f"过去 {days} 天" if days else "全部"
    lines = []
    lines.append(f"# bibigpt 现状报告 · {datetime.now().strftime('%Y-%m-%d %H:%M')} · {days_label}")
    lines.append("")
    lines.append(f"> 自动生成：`scripts/bibi-status-report.py` · 数据源：logs/bibi-calls.jsonl + logs/failed-channels.jsonl")
    lines.append("")

    # 1. 整体使用
    lines.append("## 1. 整体使用")
    lines.append("")
    lines.append("| 指标 | 数值 |")
    lines.append("|---|---|")
    lines.append(f"| 调用次数 | {len(calls)} 次 |")
    lines.append(f"| 累计扣费 | {total_cost_sec} 秒 = {total_cost_min:.1f} 分钟 |")
    lines.append("")
    lines.append("按命令分布：")
    lines.append("")
    lines.append("| 命令 | 次数 | 累计扣费 (秒) |")
    lines.append("|---|---|---|")
    for cmd, count in by_cmd.most_common():
        cmd_cost = sum(r.get("cost_duration", 0) for r in calls if r["command"] == cmd)
        lines.append(f"| `{cmd}` | {count} | {cmd_cost} |")
    lines.append("")

    # 2. 可用性
    lines.append("## 2. 可用性（get-subtitle + summarize）")
    lines.append("")
    lines.append("| 指标 | 数值 |")
    lines.append("|---|---|")
    lines.append(f"| 总调用 | {len(gs_calls)} 次 |")
    lines.append(f"| `available=true` | {gs_available_true} 次 |")
    lines.append(f"| `available=false` | {gs_available_false} 次 |")
    lines.append(f"| 可用率 | **{avail_rate:.1f}%** |")
    lines.append("")

    if gs_available_false > 0:
        lines.append("### 不可用原因 Top 5")
        lines.append("")
        reason_counter = Counter()
        for r in gs_calls:
            if not r["available"]:
                # reason 字段可能很长，截断到前 50 字
                reason = r.get("reason", "unknown")[:80]
                reason_counter[reason] += 1
        lines.append("| 原因 | 次数 |")
        lines.append("|---|---|")
        for reason, count in reason_counter.most_common(5):
            lines.append(f"| {reason} | {count} |")
        lines.append("")

    # 3. Hallucination
    lines.append("## 3. Hallucination 检测（summarize 专用）")
    lines.append("")
    lines.append("| 指标 | 数值 |")
    lines.append("|---|---|")
    lines.append(f"| summarize 调用 | {len(sm_calls)} 次 |")
    lines.append(f"| `is_hallucination=true` | {sm_hallucination} 次 |")
    lines.append(f"| Hallucination 率 | **{halluc_rate:.1f}%** |")
    lines.append("")

    if halluc_urls:
        lines.append("### 被检测为 hallucination 的视频")
        lines.append("")
        lines.append("| URL | 原因 |")
        lines.append("|---|---|")
        for url, reason in halluc_urls[:10]:
            lines.append(f"| {url[:80]} | {reason[:80]} |")
        lines.append("")

    # 4. 失败频道
    lines.append("## 4. RSS 失败频道")
    lines.append("")
    if not streak_lines:
        lines.append("✅ 无失败记录")
    else:
        lines.append("| 频道 | 连续失败天数 | 失败日期 |")
        lines.append("|---|---|---|")
        for title, n, dates in streak_lines:
            emoji = "🔴" if n >= 3 else "🟡" if n >= 2 else "🟢"
            dates_str = ", ".join(dates[-3:])  # 只显示最近 3 天
            lines.append(f"| {emoji} {title} | {n} | {dates_str} |")
        lines.append("")

    # 5. 额度消耗（按天）
    lines.append("## 5. 额度消耗（按天）")
    lines.append("")
    if by_date:
        lines.append("| 日期 | 调用次数 | 扣费 (秒) | 扣费 (分钟) |")
        lines.append("|---|---|---|---|")
        for date in sorted(by_date.keys()):
            d = by_date[date]
            lines.append(f"| {date} | {d['count']} | {d['cost_sec']} | {d['cost_sec']/60:.1f} |")
        lines.append("")

    # 6. 建议
    lines.append("## 6. 建议")
    lines.append("")
    for s in suggestions:
        lines.append(f"- {s}")
    lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="bibigpt 现状报告")
    parser.add_argument("--out", help="输出到文件（默认 stdout）")
    parser.add_argument("--days", type=int, help="只看最近 N 天")
    args = parser.parse_args()

    report = gen_report(args.days)

    if args.out:
        Path(args.out).write_text(report, encoding="utf-8")
        print(f"✅ 报告已写入：{args.out}")
    else:
        print(report)


if __name__ == "__main__":
    main()