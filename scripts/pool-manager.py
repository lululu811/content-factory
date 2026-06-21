#!/usr/bin/env python3
"""
scripts/pool-manager.py
选题池管理脚本

用法：
  python3 pool-manager.py --list                      # 列出所有选题
  python3 pool-manager.py --add --title X --moc Y    # 添加选题
  python3 pool-manager.py --mark-done --title X     # 标记完成
  python3 pool-manager.py --weekly-pick               # 本周推荐
"""

import json
import re
import argparse
from datetime import datetime
from pathlib import Path

POOL_FILE = Path('/Users/chenlei/content-factory/topics-pool.md')

PRIORITY_SCORE = {'high': 10, 'medium': 5, 'low': 2}


def parse_pool():
    """从 markdown 池子文件解析"""
    if not POOL_FILE.exists():
        return {}
    content = POOL_FILE.read_text()
    pool = {}

    current_moc = None
    current_section = None
    for line in content.split('\n'):
        if line.startswith('### '):
            current_moc = line[4:].strip()
            pool[current_moc] = {'moc': current_moc, 'topics': [], 'published': [], 'pending': []}
        elif current_moc:
            # 解析 - [ ] 选题
            m = re.match(r'^\s*- \[ \] \*\*([^*]+)\*\*[:：]?\s*(.*)$', line)
            if m:
                pool[current_moc]['pending'].append({
                    'title': m.group(1).strip(),
                    'notes': m.group(2).strip(),
                    'priority': 'medium',
                    'added_at': datetime.now().isoformat()
                })
            # 解析 ✅ 已发布
            m = re.match(r'^\s*- \[x\] \*\*([^*]+)\*\*.*$', line, re.IGNORECASE)
            if m:
                pool[current_moc]['published'].append({
                    'title': m.group(1).strip(),
                    'completed_at': datetime.now().isoformat()
                })

    return pool


def cmd_list(args):
    pool = parse_pool()
    print(f"📋 选题池：{len(pool)} 个 MOC")
    print()
    for moc, data in pool.items():
        pending = len(data.get('pending', []))
        published = len(data.get('published', []))
        print(f"  {moc}")
        print(f"    待写：{pending} | 已发布：{published}")
        for t in data.get('pending', [])[:3]:
            print(f"      - {t['title']}")


def cmd_add(args):
    pool = parse_pool()
    if args.moc not in pool:
        pool[args.moc] = {'moc': args.moc, 'topics': [], 'pending': []}
    pool[args.moc]['pending'].append({
        'title': args.title,
        'notes': args.notes or '',
        'priority': args.priority or 'medium',
        'added_at': datetime.now().isoformat()
    })
    print(f"✅ 已添加到 {args.moc}: {args.title}")


def cmd_mark_done(args):
    pool = parse_pool()
    for moc, data in pool.items():
        data['pending'] = [t for t in data['pending'] if t['title'] != args.title]
        if any(t['title'] == args.title for t in data.get('pending', [])):
            continue
        if not any(p['title'] == args.title for p in data.get('published', [])):
            data.setdefault('published', []).append({
                'title': args.title,
                'article_slug': args.article_slug or '',
                'completed_at': datetime.now().isoformat()
            })
            print(f"✅ {args.title} → 已发布（{args.article_slug or '未指定 slug'}）")
            return
    print(f"⚠️ 未找到选题：{args.title}")


def cmd_weekly_pick(args):
    pool = parse_pool()
    candidates = []
    for moc, data in pool.items():
        for t in data.get('pending', []):
            score = PRIORITY_SCORE.get(t.get('priority', 'medium'), 5)
            candidates.append({
                'moc': moc,
                'title': t['title'],
                'notes': t.get('notes', ''),
                'priority': t.get('priority', 'medium'),
                'score': score
            })
    candidates.sort(key=lambda x: -x['score'])
    print(f"📋 本周选题推荐（按优先级排序）")
    print()
    for i, c in enumerate(candidates[:10], 1):
        medals = {1: '🥇', 2: '🥈', 3: '🥉'}
        medal = medals.get(i, '  ')
        print(f"{medal} #{i}  [{c['priority']}] {c['title']}")
        print(f"        MOC: {c['moc']}")
        if c['notes']:
            print(f"        备注: {c['notes']}")
        print()


def main():
    parser = argparse.ArgumentParser(description='选题池管理')
    sub = parser.add_subparsers(dest='cmd', required=True)

    sub.add_parser('list', help='列出所有选题')

    p_add = sub.add_parser('add', help='添加选题')
    p_add.add_argument('--title', required=True)
    p_add.add_argument('--moc', required=True)
    p_add.add_argument('--priority', choices=['high', 'medium', 'low'], default='medium')
    p_add.add_argument('--notes', default='')

    p_done = sub.add_parser('mark-done', help='标记已完成')
    p_done.add_argument('--title', required=True)
    p_done.add_argument('--article-slug', default='')

    sub.add_parser('weekly-pick', help='本周推荐')

    args = parser.parse_args()
    cmd_map = {
        'list': cmd_list,
        'add': cmd_add,
        'mark-done': cmd_mark_done,
        'weekly-pick': cmd_weekly_pick,
    }
    cmd_map[args.cmd](args)


if __name__ == '__main__':
    main()