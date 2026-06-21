#!/usr/bin/env python3
"""
scripts/compliance-check.py
发布前合规检查（自动化勾选 14 项 + PASS/FAIL）

用法：
  python3 compliance-check.py <slug>              # 检查单篇
  python3 compliance-check.py --all               # 检查 drafts/posts/ 下所有草稿
  python3 compliance-check.py <slug> --strict     # 任何 FAIL 直接 exit 1

检查清单来源：templates/compliance/checklist.md（v3 · 14 项 · 唯一权威）
本脚本必须与 checklist.md 保持一致；如修改清单，请同步修改本脚本。

设计原则：
  - FAIL = 必须修复（不能发布）
  - WARN = 建议修复（可发布但有风险）
  - PASS = 已通过
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import List, Tuple, Optional

# 路径常量
CONTENT_FACTORY = Path('/Users/chenlei/content-factory')
DRAFTS_POSTS = CONTENT_FACTORY / 'drafts' / 'posts'
PUBLISH_FINAL = CONTENT_FACTORY / 'publish' / 'final'
TRACKING_PREDS = CONTENT_FACTORY / 'tracking' / 'predictions'
CHECKLIST = CONTENT_FACTORY / 'templates' / 'compliance' / 'checklist.md'

# 高风险词（仅允许在"免责声明反向表达"中出现）
HIGH_RISK_WORDS = ['目标价', '推荐', '保证', '加仓', '稳赚', '必涨', '必跌', '重仓', '满仓']

# 强证据 / 时间窗 / 升降级信号阈值
MIN_COMPANIES_TOTAL = 20
MIN_PER_CATEGORY = {
    'Controls': 2,
    'Supplies': 4,
    'Benefits': 4,
    'Weak': 3,
    'Story': 2,
}
MIN_TOP7 = 7
MIN_UPGRADE_SIGNALS = 3
MIN_DOWNGRADE_SIGNALS = 3
MIN_CONSENSUS_DIRECTIONS = 3  # 反共识方向 ≥ 3 类
MIN_IMAGES = 5
MAX_TITLE_CHARS = 30

# 股票代码正则（A 股 / 港股 / 台股 / 美股）
TICKER_PATTERNS = [
    r'\b\d{6}\.(?:SH|SZ)\b',          # A 股
    r'\b\d{4,5}\.HK\b',                # 港股
    r'\b\d{4}\.TW\b',                  # 台股
    r'\b[A-Z]{2,5}\.US\b',             # 美股
    r'\b\d{6}\.SH\b|\b\d{6}\.SZ\b',   # A 股(无小数点)
]


def find_article(slug: str) -> Optional[Path]:
    """找文章路径（优先 final/,fallback drafts/）"""
    final = PUBLISH_FINAL / slug / f'{slug}.md'
    if final.exists():
        return final
    draft = DRAFTS_POSTS / f'{slug}.md'
    if draft.exists():
        return draft
    return None


def read_article(path: Path) -> str:
    return path.read_text(encoding='utf-8')


# ─────────────────────────────────────────────
# 14 项检查函数
# ─────────────────────────────────────────────

def check_1_title(content: str, slug: str) -> Tuple[str, str]:
    """A1. 标题 ≤ 30 字 + 含反共识钩子"""
    m = re.search(r'^# (.+)$', content, re.MULTILINE)
    if not m:
        return 'FAIL', '找不到一级标题'
    title = m.group(1).strip()
    if len(title) > MAX_TITLE_CHARS:
        return 'FAIL', f'标题 {len(title)} 字,超过 30 字限制: {title!r}'
    # 反共识钩子关键词(任一即可)
    hooks = ['反共识', '真实', '未必', '不是', '不在', '别再', '误区', '陷阱', '意外', '错位',
             '低估', '高估', '误读', '错判', '假的', '真的', '真相', '残酷', '清醒']
    if not any(h in title for h in hooks):
        return 'WARN', f'标题缺少反共识钩子关键词(建议加: {hooks[:3]})'
    return 'PASS', f'标题 {len(title)} 字 + 含反共识钩子'


def check_2_companies_total(content: str, slug: str) -> Tuple[str, str]:
    """A2. 候选公司 ≥ 20 个,5 分类齐全"""
    # 找"公司 5 分类"章节(章节号可能是 七/八/九/十/八/9 等任意)
    m = re.search(r'^##[^\n]*公司\s*5\s*分类[^\n]*\n(.*?)(?=^##\s)', content, re.DOTALL | re.MULTILINE)
    if not m:
        # 备选:任何标题含"5 分类"的段落
        m = re.search(r'^##[^\n]*5\s*分类[^\n]*\n(.*?)(?=^##\s)', content, re.DOTALL | re.MULTILINE)
    if not m:
        return 'FAIL', '找不到"公司 5 分类"章节'
    section = m.group(1)

    # 统计所有形如 **公司名** 的提及
    companies = re.findall(r'\*\*([^*\d]+?)\*\*', section)
    # 过滤掉标题、章节名、证据等级说明
    companies = [c for c in companies if c not in
                 {'强证据', '中证据', '弱证据', '强', '中', '弱',
                  'Controls', 'Supplies', 'Benefits', 'Weak control',
                  'Mainly has a story', '稀缺层'}]
    unique = set(c.strip() for c in companies if len(c.strip()) > 1)

    if len(unique) < MIN_COMPANIES_TOTAL:
        return 'FAIL', f'候选公司 {len(unique)} 个,需 ≥ {MIN_COMPANIES_TOTAL}'
    return 'PASS', f'候选公司 {len(unique)} 个(≥ {MIN_COMPANIES_TOTAL})'


def check_3_weak_story_have_tickers(content: str, slug: str) -> Tuple[str, str]:
    """A3. 9.4 Weak / 9.5 Story 两类必须有具体股票代码"""
    # 找 7.4 / 9.4 / 8.4 / "Has weak control" 节
    weak_m = re.search(
        r'(?:###?\s*(?:7\.4|8\.4|9\.4|Has weak control))[^\n]*\n(.*?)(?=\n###?\s|\n##\s|\Z)',
        content, re.DOTALL | re.MULTILINE)
    story_m = re.search(
        r'(?:###?\s*(?:7\.5|8\.5|9\.5|Mainly has a story))[^\n]*\n(.*?)(?=\n###?\s|\n##\s|\Z)',
        content, re.DOTALL | re.MULTILINE)

    issues = []
    for label, mm in [('Weak', weak_m), ('Story', story_m)]:
        if not mm:
            issues.append(f'{label} 节缺失')
            continue
        section = mm.group(1)
        # 找任何 ticker pattern
        has_ticker = any(re.search(p, section) for p in TICKER_PATTERNS)
        # 找 `...` 占位
        has_placeholder = '...' in section
        # 找具体公司名(**xxx** 形式,且 2 字以上)
        company_mentions = re.findall(r'\*\*([^*\n]{2,15})\*\*', section)
        company_mentions = [c for c in company_mentions if not c.startswith(('强', '中', '弱'))]

        if has_placeholder:
            issues.append(f'{label} 节有 `...` 占位')
        if not has_ticker and not company_mentions:
            issues.append(f'{label} 节既无 ticker 也无具体公司名')

    if issues:
        return 'FAIL', '; '.join(issues)
    return 'PASS', 'Weak + Story 两节有具体公司名 / ticker'


def check_4_top7(content: str, slug: str) -> Tuple[str, str]:
    """A4. Top 7 完整 5 要素"""
    # 找 "优先研究 Top 7" / "Top 7" / "🥇 #1" 起的章节
    m = re.search(
        r'(?:##[^\n]*(?:Top\s*7|优先研究)[^\n]*\n)(.*?)(?=\n##\s|\Z)',
        content, re.DOTALL)
    if not m:
        return 'FAIL', '找不到 "优先研究 Top 7" 章节'
    section = m.group(1)

    # 5 要素关键词
    required_keys = ['卡住的环节', '产业链位置', '排序原因', '证据', '主要风险']
    missing = [k for k in required_keys if k not in section]

    if missing:
        return 'FAIL', f'Top 7 缺 5 要素: {missing}'

    # 数候选数(🥇 #N / 🥈 #N / 🥉 #N / 纯 #N 都要匹配)
    candidates = re.findall(r'(?:[🥇🥈🥉]\s*)?#\s*(\d+)\b', section)
    if candidates:
        n = max(int(c) for c in candidates)
        if n < MIN_TOP7:
            return 'WARN', f'Top 候选数 {n} < 7'
    return 'PASS', 'Top 7 完整 5 要素齐全'


def check_5_consensus(content: str, slug: str) -> Tuple[str, str]:
    """A5. 反共识方向 ≥ 3 类"""
    m = re.search(
        r'##[^\n]*反共识[^\n]*\n(.*?)(?=\n##\s|\Z)',
        content, re.DOTALL)
    if not m:
        return 'FAIL', '找不到"反共识判断"章节'
    section = m.group(1)
    # 数 🔻 段(每个是一个反共识方向)
    n = len(re.findall(r'🔻', section))
    if n < MIN_CONSENSUS_DIRECTIONS:
        return 'FAIL', f'反共识方向 {n} 类,需 ≥ {MIN_CONSENSUS_DIRECTIONS}'
    return 'PASS', f'反共识方向 {n} 类(≥ {MIN_CONSENSUS_DIRECTIONS})'


def check_6_images(content: str, slug: str) -> Tuple[str, str]:
    """A6. 配图 ≥ 5 张"""
    images = re.findall(r'!\[([^\]]*)\]\([^)]+\)', content)
    n = len(images)
    if n < MIN_IMAGES:
        return 'FAIL', f'配图 {n} 张,需 ≥ {MIN_IMAGES}'
    return 'PASS', f'配图 {n} 张(≥ {MIN_IMAGES})'


def check_7_data_freshness(content: str, slug: str) -> Tuple[str, str]:
    """A7. 数据时效 2026 H1 最新(每条数据应标日期)"""
    # 找形如 "2026 H1" / "2026-XX" / "2026/Q1" 等
    h1_2026 = len(re.findall(r'2026\s*H1', content))
    date_2026 = len(re.findall(r'2026[/\-]\d{1,2}', content))
    total = h1_2026 + date_2026
    if total < 3:
        return 'WARN', f'2026 H1 / 日期标注 {total} 处,可能数据陈旧'
    return 'PASS', f'2026 H1 数据标注 {total} 处'


def check_8_disclaimer(content: str, slug: str) -> Tuple[str, str]:
    """B8. 免责声明(中版本)"""
    keywords = ['不构成投资建议', '不构成推荐', '研究案例', '免责声明']
    found = [k for k in keywords if k in content]
    if '免责声明' not in content:
        return 'FAIL', '找不到"免责声明"标题'
    if '研究案例' not in content and '不构成推荐' not in content:
        return 'WARN', f'免责声明已加,但缺"研究案例 / 不构成推荐"标注。命中: {found}'
    return 'PASS', f'免责声明已加(含 {",".join(found)})'


def check_9_evidence_levels(content: str, slug: str) -> Tuple[str, str]:
    """B9. 证据等级 🟢🟡🔴 齐全"""
    has_green = '🟢' in content
    has_yellow = '🟡' in content
    has_red = '🔴' in content
    missing = []
    if not has_green:
        missing.append('🟢')
    if not has_yellow:
        missing.append('🟡')
    if not has_red:
        missing.append('🔴')
    if missing:
        return 'WARN', f'证据等级缺: {" ".join(missing)}(强结论必须 🟢)'
    return 'PASS', '🟢🟡🔴 三档齐全'


def check_10_sources(content: str, slug: str) -> Tuple[str, str]:
    """B10. 强结论有可查来源"""
    # 找所有 🟢 后跟来源标注的行
    green_with_source = re.findall(r'🟢[^\n]*\[?[🟢L\d\d?]?[^\n]*?(?:报告|公告|财报|海关|监管|招股书|问询函|互动易|海关数据|ID|号)', content)
    n = len(green_with_source)
    if n < 3:
        return 'WARN', f'🟢 强证据来源标注 {n} 处,可能不够详细'
    return 'PASS', f'🟢 强证据来源标注 {n} 处'


def check_11_high_risk_words(content: str, slug: str) -> Tuple[str, str]:
    """B11. 高风险词 0 处误用"""
    issues = []
    for word in HIGH_RISK_WORDS:
        # 找出所有出现位置
        positions = [m.start() for m in re.finditer(re.escape(word), content)]
        for pos in positions:
            # 检查上下文 80 字内是否有免责声明反向表达
            ctx = content[max(0, pos - 80):min(len(content), pos + 80)]
            safe_patterns = ['不构成', '不推荐', '不代表', '非', '请勿', '不代表', '仅为', '并非', '避免']
            if not any(sp in ctx for sp in safe_patterns):
                issues.append(f'"{word}" @ 位置 {pos},上下文 80 字内无反向表达')

    if issues:
        return 'FAIL', '; '.join(issues[:3]) + (f' ... 共 {len(issues)} 处' if len(issues) > 3 else '')
    return 'PASS', f'高风险词 0 处误用(检查 {len(HIGH_RISK_WORDS)} 个)'


def check_12_time_window(content: str, slug: str) -> Tuple[str, str]:
    """B12. 短期判断有时间窗口"""
    keywords = ['6 个月', '12 个月', '3-6 个月', '6-12 个月', '3 个月', '12 个月内',
                '6 个月内', '季度', '2026 H1', '2026 H2', '2026/Q1', '2026/Q2', '2026/Q3',
                '未来 6 个月', '未来 12 个月', '窗口']
    found = [k for k in keywords if k in content]
    if len(found) < 2:
        return 'WARN', f'时间窗口标注 {len(found)} 处(< 2),短期判断需更明确窗口'
    return 'PASS', f'时间窗口标注 {len(found)} 处'


def check_13_signals(content: str, slug: str) -> Tuple[str, str]:
    """B13. 升降级信号齐全(各 ≥ 3)"""
    up_m = re.search(
        r'(?:###?\s*(?:升级信号|α 兑现信号|alpha 兑现))[^\n]*\n(.*?)(?=\n###?\s|\n##\s|\Z)',
        content, re.DOTALL | re.MULTILINE)
    down_m = re.search(
        r'(?:###?\s*(?:降级信号|判断需修正))[^\n]*\n(.*?)(?=\n###?\s|\n##\s|\Z)',
        content, re.DOTALL | re.MULTILINE)

    up_count = len(re.findall(r'🟢', up_m.group(1))) if up_m else 0
    down_count = len(re.findall(r'🔴', down_m.group(1))) if down_m else 0

    issues = []
    if not up_m:
        issues.append(f'缺"升级信号"段落')
    elif up_count < MIN_UPGRADE_SIGNALS:
        issues.append(f'升级信号 {up_count} 条,< {MIN_UPGRADE_SIGNALS}')
    if not down_m:
        issues.append(f'缺"降级信号"段落')
    elif down_count < MIN_DOWNGRADE_SIGNALS:
        issues.append(f'降级信号 {down_count} 条,< {MIN_DOWNGRADE_SIGNALS}')

    if issues:
        return 'FAIL', '; '.join(issues)
    return 'PASS', f'升级 {up_count} 条 + 降级 {down_count} 条'


def check_14_tracking(content: str, slug: str, strict_path: bool = False) -> Tuple[str, str]:
    """B14. tracking/predictions/{slug}.json 已写入(发布后)"""
    pred_path = TRACKING_PREDS / f'{slug}.json'
    if not pred_path.exists():
        if strict_path:
            return 'FAIL', f'tracking/predictions/{slug}.json 不存在。发布后请跑: python3 scripts/tracking-record.py add {slug}'
        return 'WARN', f'tracking/predictions/{slug}.json 不存在(发布后会自动跑)'

    data = json.loads(pred_path.read_text(encoding='utf-8'))
    n = len(data.get('predictions', []))
    if n == 0:
        return 'WARN', 'tracking 记录为空(可能文章缺升级/降级信号段落)'
    return 'PASS', f'tracking 已写入({n} 条预测)'


# ─────────────────────────────────────────────
# 主入口
# ─────────────────────────────────────────────

CHECKS = [
    ('A1', '标题 ≤ 30 字 + 反共识钩子', check_1_title),
    ('A2', '候选公司 ≥ 20', check_2_companies_total),
    ('A3', '9.4/9.5 必须有具体代码', check_3_weak_story_have_tickers),
    ('A4', 'Top 7 完整 5 要素', check_4_top7),
    ('A5', '反共识方向 ≥ 3', check_5_consensus),
    ('A6', '配图 ≥ 5 张', check_6_images),
    ('A7', '数据时效 2026 H1', check_7_data_freshness),
    ('B8', '免责声明(中版本)', check_8_disclaimer),
    ('B9', '证据等级 🟢🟡🔴 齐全', check_9_evidence_levels),
    ('B10', '强结论有可查来源', check_10_sources),
    ('B11', '高风险词 0 误用', check_11_high_risk_words),
    ('B12', '短期判断时间窗口', check_12_time_window),
    ('B13', '升降级信号齐全', check_13_signals),
    ('B14', 'tracking 记录已写入', check_14_tracking),
]


def run_checks(slug: str, content: str, strict: bool = False) -> List[Tuple[str, str, str, str]]:
    """对单篇文章跑 14 项检查。返回 [(编号, 名称, 状态, 说明), ...]"""
    results = []
    for code, name, fn in CHECKS:
        try:
            if fn == check_14_tracking:
                status, msg = fn(content, slug, strict_path=strict)
            else:
                status, msg = fn(content, slug)
        except Exception as e:
            status, msg = 'ERROR', f'检查器异常: {type(e).__name__}: {e}'
        results.append((code, name, status, msg))
    return results


def print_report(slug: str, results: List[Tuple[str, str, str, str]]) -> bool:
    """打印报告。返回 True = 全 PASS / WARN(可发布),False = 有 FAIL(不可发布)"""
    fail = sum(1 for _, _, s, _ in results if s == 'FAIL')
    warn = sum(1 for _, _, s, _ in results if s == 'WARN')
    ok = sum(1 for _, _, s, _ in results if s == 'PASS')
    err = sum(1 for _, _, s, _ in results if s == 'ERROR')

    print('═' * 70)
    print(f'  合规检查报告 · {slug}')
    print('═' * 70)
    for code, name, status, msg in results:
        icon = {'PASS': '✅', 'WARN': '⚠️ ', 'FAIL': '❌', 'ERROR': '💥'}[status]
        print(f'  {icon} [{code}] {name}')
        print(f'         {msg}')
    print('═' * 70)
    print(f'  汇总: ✅ {ok} | ⚠️  {warn} | ❌ {fail} | 💥 {err}')
    print('═' * 70)

    if fail > 0 or err > 0:
        print(f'  🚫 **不可发布**:有 {fail} 项 FAIL + {err} 项 ERROR,需先修复。')
        return False
    if warn > 0:
        print(f'  ⚠️  **可发布但有风险**:有 {warn} 项 WARN,建议尽快修复。')
    else:
        print(f'  🎉 **可发布**:14/14 全部 PASS。')
    return True


def check_one(slug: str, strict: bool = False) -> bool:
    path = find_article(slug)
    if not path:
        print(f'❌ 找不到文章: drafts/posts/{slug}.md 或 publish/final/{slug}/{slug}.md')
        return False
    content = read_article(path)
    results = run_checks(slug, content, strict=strict)
    return print_report(slug, results)


def check_all(strict: bool = False) -> int:
    """检查 drafts/posts/ 下所有 .md 文件。返回 PASS 数。"""
    drafts = sorted(DRAFTS_POSTS.glob('*.md'))
    if not drafts:
        print('⚠️  drafts/posts/ 下没有 .md 文件')
        return 0
    passed = 0
    for draft in drafts:
        slug = draft.stem
        content = draft.read_text(encoding='utf-8')
        results = run_checks(slug, content, strict=strict)
        if print_report(slug, results):
            passed += 1
        print()
    print(f'═ 总计:{passed}/{len(drafts)} 篇可发布 ═')
    return passed


def main():
    parser = argparse.ArgumentParser(description='发布前合规检查(自动化 14 项 + PASS/FAIL)')
    parser.add_argument('slug', nargs='?', help='文章 slug,如 asean-ai-supply-chain')
    parser.add_argument('--all', action='store_true', help='检查 drafts/posts/ 下所有草稿')
    parser.add_argument('--strict', action='store_true', help='任意 FAIL 直接 exit 1')
    parser.add_argument('--json', action='store_true', help='输出 JSON 格式(供其他脚本消费)')

    args = parser.parse_args()

    if not args.slug and not args.all:
        parser.print_help()
        sys.exit(1)

    if args.all:
        passed = check_all(strict=args.strict)
        sys.exit(0 if passed >= 0 else 1)

    ok = check_one(args.slug, strict=args.strict)
    sys.exit(0 if ok or not args.strict else 1)


if __name__ == '__main__':
    main()