#!/usr/bin/env python3
"""
scripts/tracking-record.py
跟踪表记录系统

用法：
  python3 tracking-record.py --add <article-slug>
  python3 tracking-record.py --list
  python3 tracking-record.py --show <slug>
  python3 tracking-record.py --verify <slug> --id <pred_id> --status <verified/failed/partial>

设计：
  - 每篇文章发布时，从文章里提取"可验证判断"（升降级信号、核心数据预测）
  - 设置验证日期（3/6/12 个月后）
  - 季度自动回看，更新战绩表
"""

import json
import re
import os
from datetime import datetime, timedelta
from pathlib import Path

TRACKING_DIR = Path(os.path.expanduser('~/content-factory/tracking'))
PRED_DIR = TRACKING_DIR / 'predictions'
PRED_DIR.mkdir(parents=True, exist_ok=True)


def parse_article_predictions(slug):
    """从发布包文章里提取可验证判断"""
    article_path = Path(os.path.expanduser(
        f'~/content-factory/publish/final/{slug}/{slug}.md'
    ))
    if not article_path.exists():
        article_path = Path(os.path.expanduser(
            f'~/content-factory/drafts/posts/{slug}.md'
        ))
    if not article_path.exists():
        print(f"❌ 文章不存在：{slug}")
        return None

    content = article_path.read_text()

    # 提取升级信号 + 降级信号 + 核心跟踪指标
    # 关键修复:用段落锚点(### 升级信号 / ## 升级信号 等)定位,而不是全文匹配 🟢
    # 否则"证据等级说明"里的 🟢 会被误识别成"升级信号"
    predictions = []

    def _extract_in_section(content, section_titles, emoji, pred_id_prefix, pred_type, direction):
        """在指定标题段落范围内抓取 emoji 行"""
        results = []
        for title in section_titles:
            # 匹配:## / ### / #### 标题(中英文空格都允许),锚点段到下一个同级或更高级标题
            # 注意:在 rf-string 里 #{...} 会被当成格式化表达式,所以要写 #{{...}}
            pattern = (
                rf'(?:^#{{2,4}})\s*{re.escape(title)}[^\n]*\n'  # 段头
                rf'(.*?)'                                         # 段内容(非贪婪)
                rf'(?=\n#{{1,4}}\s|\Z)'                          # 段尾:下一个标题或文件结尾
            )
            m = re.search(pattern, content, re.DOTALL | re.MULTILINE)
            if not m:
                continue
            section_body = m.group(1)
            # 在段内抓 🟢 / 🔴 行。允许可选的列表前缀(- / * / 数字.),可选 **加粗**,
            # 冒号(: 或 :)可有可无。文本里常有 "- 🟢 **xxx**（说明）" 这种写法。
            # 注意:为了避免 Python re alternation 回溯陷阱,把 detail 限定为不含 -
            # 和不含 emoji(防止意外跨行吞到下一条)。
            line_pattern = (
                rf'^[ \t]*(?:[-*+]|\d+\.)[ \t]+{emoji}[ \t]*'
                rf'(?:\*\*([^*]+)\*\*|([^\n:：（(\-]+))'
                rf'[：:]?\s*([^\n\-{emoji}]+)?'
            )
            for lm in re.finditer(line_pattern, section_body, re.MULTILINE):
                name = (lm.group(1) or lm.group(2) or '').strip()
                detail = (lm.group(3) or '').strip()
                if not name:
                    continue
                # 过滤掉"证据等级说明"里的元描述(例如:"强证据" / "中证据" / "弱证据")
                if name in {'强证据', '中证据', '弱证据', '强', '中', '弱'}:
                    continue
                statement = f'{name}: {detail}' if detail else name
                results.append({
                    'id': f'{pred_id_prefix}-{len(results)+1:02d}',
                    'statement': statement,
                    'type': pred_type,
                    'direction': direction,
                    'source': f'文章{title}段落'
                })
        return results

    # 升级信号:常见标题变体
    predictions += _extract_in_section(
        content,
        section_titles=['升级信号', '升级条件', 'α 兑现信号', 'alpha 兑现'],
        emoji='🟢',
        pred_id_prefix='UP',
        pred_type='升级信号',
        direction='up',
    )

    # 降级信号:常见标题变体
    predictions += _extract_in_section(
        content,
        section_titles=['降级信号', '降级条件', '判断需修正'],
        emoji='🔴',
        pred_id_prefix='DOWN',
        pred_type='降级信号',
        direction='down',
    )

    if not predictions:
        print(f'⚠️  未在文章里找到"升级信号"或"降级信号"段落(常见标题:升级信号 / 降级信号)。'
              f'请确认 SOP v2 模板第 12 节"风险与升级/降级信号"已写。')

    return {
        'slug': slug,
        'title': extract_title(content),
        'published_at': extract_date(content),
        'created_at': datetime.now().isoformat(),
        'predictions': predictions,
        'verification_log': []
    }


def extract_title(content):
    """提取文章标题"""
    m = re.search(r'^# (.+)$', content, re.MULTILINE)
    return m.group(1).strip() if m else ''


def extract_date(content):
    """提取 frontmatter 日期"""
    m = re.search(r'date:\s*(\d{4}-\d{2}-\d{2})', content)
    return m.group(1) if m else datetime.now().strftime('%Y-%m-%d')


def add_prediction(slug, verify_months=None):
    """添加新文章的预测记录"""
    record = parse_article_predictions(slug)
    if not record:
        return

    pub_date = datetime.strptime(record['published_at'], '%Y-%m-%d')

    # 设置验证日期（默认 3/6/12 个月）
    for p in record['predictions']:
        if verify_months:
            p['verify_at'] = (pub_date + timedelta(days=verify_months * 30)).strftime('%Y-%m-%d')
        else:
            # 默认 6 个月后验证
            p['verify_at'] = (pub_date + timedelta(days=180)).strftime('%Y-%m-%d')
        p['actual'] = None
        p['verified'] = None  # True / False / None
        p['verified_at'] = None
        p['notes'] = ''

    # 保存
    output_path = PRED_DIR / f'{slug}.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(record, f, ensure_ascii=False, indent=2)
    print(f"✅ 已记录：{output_path}")
    print(f"   标题：{record['title']}")
    print(f"   预测数：{len(record['predictions'])} 条")
    for p in record['predictions']:
        print(f"   - {p['id']} [{p['type']}] {p['statement'][:60]}... → 验证日 {p['verify_at']}")


def list_records():
    """列出所有跟踪记录"""
    files = sorted(PRED_DIR.glob('*.json'))
    if not files:
        print("暂无跟踪记录")
        return
    print(f"📋 跟踪记录：{len(files)} 篇")
    print()
    for f in files:
        with open(f) as fp:
            record = json.load(fp)
        total = len(record.get('predictions', []))
        verified = sum(1 for p in record.get('predictions', []) if p.get('verified') is not None)
        pending = sum(1 for p in record.get('predictions', []) if p.get('verify_at', '') <= datetime.now().strftime('%Y-%m-%d') and p.get('verified') is None)
        print(f"  {record['slug']}: {record['title'][:40]}...")
        print(f"    总预测: {total} | 已验证: {verified} | 待验证: {pending}")


def show_record(slug):
    """显示单篇文章的预测"""
    path = PRED_DIR / f'{slug}.json'
    if not path.exists():
        print(f"❌ 未找到：{path}")
        return
    with open(path) as f:
        record = json.load(f)
    print(f"════════════════════════════════════════")
    print(f"📋 {record['slug']}: {record['title']}")
    print(f"   发布：{record['published_at']}")
    print(f"════════════════════════════════════════")
    for p in record.get('predictions', []):
        status = '✓' if p['verified'] else ('✗' if p['verified'] is False else '○')
        print(f"\n{status} [{p['id']}] [{p['type']}]")
        print(f"   预测：{p['statement']}")
        print(f"   验证日：{p['verify_at']}")
        if p.get('verified') is not None:
            print(f"   结果：{'✓ 验证通过' if p['verified'] else '✗ 未通过'}")
            if p.get('actual'):
                print(f"   实际：{p['actual']}")
            if p.get('notes'):
                print(f"   备注：{p['notes']}")


def verify_prediction(slug, pred_id, status, actual='', notes=''):
    """更新一条预测的验证状态"""
    path = PRED_DIR / f'{slug}.json'
    if not path.exists():
        print(f"❌ 未找到：{path}")
        return
    with open(path) as f:
        record = json.load(f)

    found = False
    for p in record.get('predictions', []):
        if p['id'] == pred_id:
            p['verified'] = (status == 'verified')
            p['actual'] = actual
            p['notes'] = notes
            p['verified_at'] = datetime.now().strftime('%Y-%m-%d')
            found = True
            break

    if not found:
        print(f"❌ 预测 ID 不存在：{pred_id}")
        return

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(record, f, ensure_ascii=False, indent=2)
    print(f"✅ 已更新 {slug}/{pred_id}: {status}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='跟踪表记录系统')
    sub = parser.add_subparsers(dest='cmd', required=True)

    p_add = sub.add_parser('add', help='记录新文章')
    p_add.add_argument('slug')
    p_add.add_argument('--months', type=int, default=6, help='验证月份（默认 6）')

    sub.add_parser('list', help='列出所有记录')
    p_show = sub.add_parser('show', help='显示单篇')
    p_show.add_argument('slug')

    p_verify = sub.add_parser('verify', help='更新验证状态')
    p_verify.add_argument('slug')
    p_verify.add_argument('--id', required=True)
    p_verify.add_argument('--status', choices=['verified', 'failed', 'partial'], required=True)
    p_verify.add_argument('--actual', default='', help='实际情况描述')
    p_verify.add_argument('--notes', default='', help='备注')

    args = parser.parse_args()

    if args.cmd == 'add':
        add_prediction(args.slug, args.months)
    elif args.cmd == 'list':
        list_records()
    elif args.cmd == 'show':
        show_record(args.slug)
    elif args.cmd == 'verify':
        verify_prediction(args.slug, args.id, args.status, args.actual, args.notes)


if __name__ == '__main__':
    main()