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
    content = POOL_FILE.read_text(encoding='utf-8')
    pool = {}

    current_moc = None
    for line in content.split('\n'):
        if line.startswith('### '):
            current_moc = line[4:].strip()
            pool[current_moc] = {'moc': current_moc, 'published': [], 'pending': []}
        elif current_moc:
            # 1. 解析待写选题，支持识别优先级后缀如 **Title [high]** 或 **Title (low)**
            m_pending = re.match(r'^\s*- \[ \]\s*\*\*([^*]+)\*\*[:：]?\s*(.*)$', line)
            if m_pending:
                title_part = m_pending.group(1).strip()
                notes_part = m_pending.group(2).strip()
                
                # 从标题部分中尝试提取优先级 [high]/[low]/(high)/(low)
                priority = 'medium'
                priority_match = re.search(r'\s*[\[(](high|medium|low)[\])]$', title_part, re.IGNORECASE)
                if priority_match:
                    priority = priority_match.group(1).lower()
                    title_part = title_part[:priority_match.start()].strip()
                    
                pool[current_moc]['pending'].append({
                    'title': title_part,
                    'notes': notes_part,
                    'priority': priority,
                    'added_at': datetime.now().isoformat()
                })
                continue
            
            # 2. 解析已发布选题 (可能是行内形式，也可能是列表形式)
            # 行内形式如: **已发布**：✅ 2026-06-20：摩根士丹利东盟峰会...
            if '**已发布**' in line and any(sym in line for sym in ['✅', '[x]', '[X]']):
                m_inline = re.search(r'(?:✅|\[x\]|\[X\])\s*(?:(\d{4}-\d{2}-\d{2})[：:]\s*)?(.*)$', line)
                if m_inline:
                    date_str = m_inline.group(1) or datetime.now().strftime('%Y-%m-%d')
                    title_text = m_inline.group(2).strip()
                    
                    slug = ""
                    slug_match = re.search(r'[\s（(]([a-zA-Z0-9_-]+)[\s）)]$', title_text)
                    if slug_match:
                        slug = slug_match.group(1)
                        title_text = title_text[:slug_match.start()].strip()
                        
                    pool[current_moc]['published'].append({
                        'title': title_text,
                        'completed_at': date_str,
                        'article_slug': slug
                    })
                continue

            # 列表形式如: - ✅ 2026-06-20：摩根士丹利东盟峰会...
            m_list_pub = re.match(r'^\s*-\s*(?:✅|\[x\]|\[X\])\s*(?:(\d{4}-\d{2}-\d{2})[：:]\s*)?(.*)$', line)
            if m_list_pub:
                date_str = m_list_pub.group(1) or datetime.now().strftime('%Y-%m-%d')
                title_text = m_list_pub.group(2).strip()
                
                slug = ""
                slug_match = re.search(r'[\s（(]([a-zA-Z0-9_-]+)[\s）)]$', title_text)
                if slug_match:
                    slug = slug_match.group(1)
                    title_text = title_text[:slug_match.start()].strip()
                
                pool[current_moc]['published'].append({
                    'title': title_text,
                    'completed_at': date_str,
                    'article_slug': slug
                })

    return pool


def save_pool(pool):
    """将选题池更新回 topics-pool.md 文件中的特定区域"""
    if not POOL_FILE.exists():
        print(f"❌ 选题池文件不存在：{POOL_FILE}")
        return

    content = POOL_FILE.read_text(encoding='utf-8')
    
    start_match = re.search(r'^## 一、当前选题池（按 MOC 分组）', content, re.MULTILINE)
    if not start_match:
        print("❌ 无法在 topics-pool.md 中定位'## 一、当前选题池（按 MOC 分组）'")
        return

    end_match = re.search(r'^## 二、选题池管理脚本', content, re.MULTILINE)
    if not end_match:
        next_headings = list(re.finditer(r'^## ', content, re.MULTILINE))
        for h in next_headings:
            if h.start() > start_match.end():
                end_match = h
                break
                
    if not end_match:
        print("❌ 无法在 topics-pool.md 中定位下一章节标题")
        return

    header_part = content[:start_match.start()]
    footer_part = content[end_match.start():]

    pool_lines = ["## 一、当前选题池（按 MOC 分组）\n"]
    for moc_name, data in pool.items():
        pool_lines.append(f"### {moc_name}\n")
        
        # 已发布
        pool_lines.append("**已发布**：")
        if data.get('published'):
            pool_lines.append("")
            for p in data['published']:
                slug_str = f" ({p['article_slug']})" if p.get('article_slug') else ""
                pool_lines.append(f"- ✅ {p['completed_at']}：{p['title']}{slug_str}")
        else:
            pool_lines[-1] += "无"
        pool_lines.append("")
        
        # 待写
        pool_lines.append("**待写**：")
        if data.get('pending'):
            pool_lines.append("")
            for p in data['pending']:
                priority_str = f" [{p['priority']}]" if p.get('priority') and p['priority'] != 'medium' else ""
                notes_str = f"：{p['notes']}" if p.get('notes') else ""
                pool_lines.append(f"- [ ] **{p['title']}{priority_str}**{notes_str}")
        else:
            pool_lines[-1] += "无"
        pool_lines.append("")

    pool_content = "\n".join(pool_lines) + "\n"
    new_content = header_part + pool_content + footer_part
    POOL_FILE.write_text(new_content, encoding='utf-8')
    print(f"💾 已成功将选题池保存到 {POOL_FILE}")


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
        pool[args.moc] = {'moc': args.moc, 'published': [], 'pending': []}
    pool[args.moc]['pending'].append({
        'title': args.title,
        'notes': args.notes or '',
        'priority': args.priority or 'medium',
        'added_at': datetime.now().isoformat()
    })
    save_pool(pool)
    print(f"✅ 已添加到 {args.moc}: {args.title}")


def cmd_mark_done(args):
    pool = parse_pool()
    for moc, data in pool.items():
        pending_titles = [t['title'] for t in data.get('pending', [])]
        if args.title in pending_titles:
            data['pending'] = [t for t in data['pending'] if t['title'] != args.title]
            if not any(p['title'] == args.title for p in data.get('published', [])):
                data.setdefault('published', []).append({
                    'title': args.title,
                    'article_slug': args.article_slug or '',
                    'completed_at': datetime.now().strftime('%Y-%m-%d')
                })
            save_pool(pool)
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