#!/usr/bin/env python3
"""
scripts/verify-predictions.py
季度回看 + 战绩表生成

用法：
  python3 verify-predictions.py --check-due       # 列出所有到期需验证的预测
  python3 verify-predictions.py --generate-report # 生成战绩表 markdown
  python3 verify-predictions.py --generate-report --quarter  # 季度战绩
"""

import json
import os
from datetime import datetime
from pathlib import Path

TRACKING_DIR = Path(os.path.expanduser('~/content-factory/tracking'))
PRED_DIR = TRACKING_DIR / 'predictions'
REPORTS_DIR = TRACKING_DIR / 'reports'
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def check_due():
    """列出所有到期需要验证的预测"""
    today = datetime.now().strftime('%Y-%m-%d')
    files = sorted(PRED_DIR.glob('*.json'))

    due_list = []
    for f in files:
        with open(f) as fp:
            record = json.load(fp)
        for p in record.get('predictions', []):
            if p.get('verified') is not None:
                continue
            if p.get('verify_at', '') <= today:
                due_list.append({
                    'slug': record['slug'],
                    'title': record['title'],
                    'pred_id': p['id'],
                    'type': p['type'],
                    'statement': p['statement'],
                    'verify_at': p['verify_at'],
                    'days_overdue': (datetime.now() - datetime.strptime(p['verify_at'], '%Y-%m-%d')).days
                })

    if not due_list:
        print("✅ 暂无到期未验证的预测")
        return

    due_list.sort(key=lambda x: -x['days_overdue'])
    print(f"⏰ 到期待验证：{len(due_list)} 条")
    print()
    for d in due_list:
        print(f"  [{d['pred_id']}] {d['slug']} ({d['days_overdue']} 天前到期)")
        print(f"    类型：{d['type']}")
        print(f"    预测：{d['statement'][:80]}")
        print(f"    验证日：{d['verify_at']}")
        print()


def generate_report(quarter=False):
    """生成战绩表 markdown"""
    today = datetime.now().strftime('%Y-%m-%d')
    files = sorted(PRED_DIR.glob('*.json'))

    if not files:
        print("❌ 暂无跟踪记录")
        return

    total_preds = 0
    verified_count = 0
    failed_count = 0
    pending_count = 0
    overdue_count = 0

    by_article = []
    for f in files:
        with open(f) as fp:
            record = json.load(fp)
        art_total = 0
        art_verified = 0
        art_failed = 0
        for p in record.get('predictions', []):
            total_preds += 1
            art_total += 1
            if p.get('verified') is True:
                verified_count += 1
                art_verified += 1
            elif p.get('verified') is False:
                failed_count += 1
                art_failed += 1
            else:
                pending_count += 1
                if p.get('verify_at', '') <= today:
                    overdue_count += 1
        accuracy = art_verified / (art_verified + art_failed) * 100 if (art_verified + art_failed) > 0 else 0
        by_article.append({
            'slug': record['slug'],
            'title': record['title'],
            'published_at': record.get('published_at', ''),
            'total': art_total,
            'verified': art_verified,
            'failed': art_failed,
            'pending': art_total - art_verified - art_failed,
            'accuracy': accuracy
        })

    overall_accuracy = verified_count / (verified_count + failed_count) * 100 if (verified_count + failed_count) > 0 else 0

    # 生成 markdown 报告
    period = '季度' if quarter else '累计'
    report = f"""# 战绩表 · {period}报告（截至 {today}）

> 本文公开追踪本号所有可验证判断的实际结果。**战绩是公开的，反馈是真实的**。

## 整体战绩

| 指标 | 数值 |
|---|---|
| 覆盖文章 | {len(files)} 篇 |
| 总预测数 | {total_preds} 条 |
| ✓ 已验证通过 | {verified_count} 条 |
| ✗ 未通过 | {failed_count} 条 |
| ○ 待验证 | {pending_count} 条 |
| ⚠ 已逾期未验证 | {overdue_count} 条 |
| **整体准确率** | **{overall_accuracy:.1f}%** |

## 分文章战绩

| 文章 | 发布 | 总预测 | ✓ | ✗ | ○ | 准确率 |
|---|---|---|---|---|---|---|
"""
    for a in sorted(by_article, key=lambda x: -x['accuracy']):
        report += f"| {a['title'][:30]}... | {a['published_at']} | {a['total']} | {a['verified']} | {a['failed']} | {a['pending']} | {a['accuracy']:.1f}% |\n"

    if verified_count + failed_count == 0:
        report += "\n> ⚠️ 目前还没有已验证的预测。3-6 个月后会有完整战绩。\n"
    else:
        report += f"\n## 已验证预测明细\n\n"
        for f in files:
            with open(f) as fp:
                record = json.load(fp)
            for p in record.get('predictions', []):
                if p.get('verified') is None:
                    continue
                status = '✓' if p['verified'] else '✗'
                report += f"- {status} **[{record['slug']}/{p['id']}]** {p['type']}\n"
                report += f"  - 预测：{p['statement']}\n"
                if p.get('actual'):
                    report += f"  - 实际：{p['actual']}\n"
                report += f"  - 验证日：{p.get('verified_at', '')}\n\n"

    report += f"""
---

**数据来源**：每篇文章的"跟踪指标 + 升降级信号"段落。

**验证规则**：
- 升级信号验证（trigger 到 → ✓ verified）
- 降级信号验证（trigger 到 → ✗ failed）
- 部分验证（部分 trigger → partial）

**更新机制**：季度公开一次。
"""

    # 保存
    suffix = '-quarter' if quarter else ''
    output_path = REPORTS_DIR / f'战绩表-{today}{suffix}.md'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"✅ 战绩表已生成：{output_path}")
    print()
    print(report)


def main():
    import argparse
    parser = argparse.ArgumentParser(description='季度回看 + 战绩表生成')
    parser.add_argument('--check-due', action='store_true', help='列出到期未验证的预测')
    parser.add_argument('--generate-report', action='store_true', help='生成战绩表')
    parser.add_argument('--quarter', action='store_true', help='季度战绩')
    args = parser.parse_args()

    if args.check_due:
        check_due()
    elif args.generate_report:
        generate_report(quarter=args.quarter)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()