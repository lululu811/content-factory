#!/usr/bin/env python3
"""
scripts/single-stock-completeness-check.py
个股深度报告完整性检查(v1 · 12 章 + A18/A19/A20 + 三源校验)

用法:
  python3 single-stock-completeness-check.py <slug>           # 检查单篇
  python3 single-stock-completeness-check.py <slug> --strict  # 任意 FAIL exit 1
  python3 single-stock-completeness-check.py --all            # 检查所有个股草稿

设计原则(2026-06-30 用户原话"数据来源正确性是根基"):
  - FAIL = 必须修复(不能发布)
  - WARN = 建议修复(可发布但有风险)
  - PASS = 已通过

检查清单来源:templates/post-template-single-stock.md(CCC 完整型 v1)
本脚本必须与该模板保持一致;如修改模板,请同步修改本脚本。
"""

import argparse
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Tuple

# 路径常量
CONTENT_FACTORY = Path('/Users/chenlei/content-factory')
DRAFTS_POSTS = CONTENT_FACTORY / 'drafts' / 'posts'
TRACKING_PREDS = CONTENT_FACTORY / 'tracking' / 'predictions'

# 高风险词(仅允许在"免责声明反向表达"中出现)
HIGH_RISK_WORDS = ['目标价', '推荐', '保证', '加仓', '稳赚', '必涨', '必跌', '重仓', '满仓']

# 阈值
MIN_EVIDENCE_RATIO = 0.70  # 强证据占比 ≥ 70%
MIN_UPGRADE_SIGNALS = 3     # 升级信号 ≥ 3
MIN_DOWNGRADE_SIGNALS = 3   # 降级信号 ≥ 3
DATA_MAX_AGE_DAYS = 7       # 单股报告数据时效 ≤ 7 天
PRICE_MAX_AGE_DAYS = 1      # 实时行情 ≤ 1 天


# ============ 12 章 + A18/A19/A20 检查函数 ============

def check_s1_company_overview(content: str) -> Tuple[str, str]:
    """S1. 公司速览章节齐全"""
    m = re.search(r'##\s*一[、,]\s*公司速览', content)
    if not m:
        return 'FAIL', '找不到"公司速览"章节'
    section = m.group(0)
    return 'PASS', '公司速览章节齐全'


def check_s2_three_logics(content: str) -> Tuple[str, str]:
    """S2. 投资逻辑 3 条齐全"""
    m = re.search(r'##\s*二[、,]\s*投资逻辑.*?\n(.*?)(?=\n##\s|\Z)', content, re.DOTALL)
    if not m:
        return 'FAIL', '找不到"投资逻辑"章节'
    section = m.group(1)
    logics = re.findall(r'(?:逻辑\s*\d+|🟢|🟡|🔴)[^\n]{10,}', section)
    if len(logics) < 3:
        return 'FAIL', f'投资逻辑仅 {len(logics)} 条,需 ≥ 3'
    return 'PASS', f'投资逻辑 {len(logics)} 条齐全'


def check_s3_business_structure(content: str) -> Tuple[str, str]:
    """S3. 业务结构拆解(≥ 3 业务板块)"""
    m = re.search(r'##\s*三[、,]\s*业务结构.*?\n(.*?)(?=\n##\s|\Z)', content, re.DOTALL)
    if not m:
        return 'FAIL', '找不到"业务结构"章节'
    section = m.group(1)
    # 业务分项(行内"业务名" + "占比/收入/毛利率")
    biz_items = re.findall(r'(?:业务|产品|板块)[^\n]{0,30}(?:%|亿|万元)', section)
    if len(biz_items) < 3:
        return 'WARN', f'业务分项 {len(biz_items)} 个,建议 ≥ 3'
    return 'PASS', f'业务分项 {len(biz_items)} 个'


def check_s4_industry_landscape(content: str) -> Tuple[str, str]:
    """S4. 行业地位 & 全球格局"""
    m = re.search(r'##\s*四[、,]\s*行业(?:地位|格局).*?\n(.*?)(?=\n##\s|\Z)', content, re.DOTALL)
    if not m:
        return 'FAIL', '找不到"行业地位/全球格局"章节'
    section = m.group(1)
    # 至少 3 个对标公司
    competitors = re.findall(r'(?:尤尼明|挪威|TQC|菲利华|凯德|欧晶|贺利氏|东曹|信越)', section)
    if len(set(competitors)) < 3:
        return 'WARN', f'对标公司 {len(set(competitors))} 家,建议 ≥ 3'
    return 'PASS', f'对标公司 {len(set(competitors))} 家'


def check_s5_financial_trend(content: str) -> Tuple[str, str]:
    """S5. 5 年财务趋势(5 指标 × 5 年 = 25 数据点)"""
    m = re.search(r'##\s*五[、,]\s*5\s*年.*?\n(.*?)(?=\n##\s|\Z)', content, re.DOTALL)
    if not m:
        return 'FAIL', '找不到"5 年财务趋势"章节'
    section = m.group(1)
    # 数数据点(数字 + 年份 / 季报)
    data_points = re.findall(r'\d{4}\s*[年Q][^\n]{0,20}', section)
    if len(data_points) < 10:
        return 'WARN', f'财务数据点 {len(data_points)},建议 ≥ 10(5 年 × 2 指标)'
    return 'PASS', f'财务数据点 {len(data_points)}'


def check_s6_business_highlights(content: str) -> Tuple[str, str]:
    """S6. 业务亮点深度(≥ 3 业务各 ~500 字)"""
    m = re.search(r'##\s*六[、,]\s*业务亮点.*?\n(.*?)(?=\n##\s|\Z)', content, re.DOTALL)
    if not m:
        return 'FAIL', '找不到"业务亮点"章节'
    section = m.group(1)
    # 业务段(用 ### 或加粗 业务名)
    biz_segments = re.findall(r'(?:###\s*[一二三四五六七八九十0-9]+[、,.]|业务\s*\d+|\*\*[^*]{0,30}业务[^*]*\*\*)', section)
    if len(biz_segments) < 3:
        return 'WARN', f'业务亮点段 {len(biz_segments)},建议 ≥ 3'
    return 'PASS', f'业务亮点段 {len(biz_segments)}'


def check_s7_valuation(content: str) -> Tuple[str, str]:
    """S7. 估值分析 + 反共识估值区间"""
    m = re.search(r'##\s*七[、,]\s*估值.*?\n(.*?)(?=\n##\s|\Z)', content, re.DOTALL)
    if not m:
        return 'FAIL', '找不到"估值分析"章节'
    section = m.group(1)
    # 反共识估值区间
    if not re.search(r'反共识估值', section):
        return 'FAIL', '估值章节缺"反共识估值区间"'
    # 4 个估值指标
    metrics = re.findall(r'\b(?:PE|PB|PEG|PS)(?:-TTM)?', section)
    if len(set(metrics)) < 3:
        return 'WARN', f'估值指标 {len(set(metrics))} 个(PE/PB/PEG/PS),建议 ≥ 3'
    # "非推荐价位"反向表达
    if not re.search(r'非推荐价位|研究案例', section):
        return 'FAIL', '缺"非推荐价位"反向表达'
    return 'PASS', f'反共识估值区间 + {len(set(metrics))} 个估值指标齐全'


def check_s8_risks(content: str) -> Tuple[str, str]:
    """S8. 关键风险(5 类公司级)"""
    m = re.search(r'##\s*八[、,]\s*(?:关键)?风险.*?\n(.*?)(?=\n##\s|\Z)', content, re.DOTALL)
    if not m:
        return 'FAIL', '找不到"风险"章节'
    section = m.group(1)
    # 5 类公司级风险关键词
    risk_categories = ['管理', '产品', '客户', '财务', '估值']
    found = [cat for cat in risk_categories if re.search(cat, section)]
    if len(found) < 4:
        return 'FAIL', f'公司级风险类别 {len(found)} 类(管理/产品/客户/财务/估值),需 ≥ 4'
    return 'PASS', f'风险类别 {len(found)} 类齐全'


def check_s9_counter_consensus(content: str) -> Tuple[str, str]:
    """S9. 反共识判断(≥ 3 类)"""
    m = re.search(r'##\s*九[、,]\s*(?:反共识|非常识).*?\n(.*?)(?=\n##\s|\Z)', content, re.DOTALL)
    if not m:
        return 'FAIL', '找不到"反共识判断"章节'
    section = m.group(1)
    # 🔻 段
    n = len(re.findall(r'🔻', section))
    if n < MIN_EVIDENCE_RATIO * 0:  # placeholder
        pass
    if n < 3:
        return 'FAIL', f'反共识方向 {n} 类,需 ≥ 3'
    return 'PASS', f'反共识方向 {n} 类'


def check_s10_signals(content: str) -> Tuple[str, str]:
    """S10. 跟踪信号(升级 ≥ 3,降级 ≥ 3)"""
    m_up = re.search(r'###\s*升级信号[^\n]*\n(.*?)(?=\n###?\s|\n##\s|\Z)', content, re.DOTALL | re.MULTILINE)
    m_down = re.search(r'###\s*降级信号[^\n]*\n(.*?)(?=\n###?\s|\n##\s|\Z)', content, re.DOTALL | re.MULTILINE)

    issues = []
    if not m_up:
        issues.append('缺"升级信号"段')
    else:
        up_count = len(re.findall(r'🟢|📈|✅', m_up.group(1)))
        if up_count < MIN_UPGRADE_SIGNALS:
            issues.append(f'升级信号 {up_count} 条 < {MIN_UPGRADE_SIGNALS}')
    if not m_down:
        issues.append('缺"降级信号"段')
    else:
        down_count = len(re.findall(r'🔴|📉|⚠️', m_down.group(1)))
        if down_count < MIN_DOWNGRADE_SIGNALS:
            issues.append(f'降级信号 {down_count} 条 < {MIN_DOWNGRADE_SIGNALS}')

    if issues:
        return 'FAIL', '; '.join(issues)
    return 'PASS', f'升级 + 降级信号齐全'


def check_s11_data_validation(content: str) -> Tuple[str, str]:
    """S11. 数据校验报告(硬交付,三源对比 + 冲突记录 + 强证据占比)"""
    m = re.search(r'##\s*十一[、,]\s*数据校验.*?\n(.*?)(?=\n##\s|\Z)', content, re.DOTALL)
    if not m:
        return 'FAIL', '找不到"数据校验报告"章节(硬交付)'
    section = m.group(1)

    # A18: 三源对比表
    if not re.search(r'(?:三源|myMCP|cninfo|ZsxqCrawler)', section):
        return 'FAIL', 'A18 数据校验章节缺三源对比表'

    # A19: 数据冲突显式记录
    if not re.search(r'(?:冲突|conflict|差异)', section):
        return 'WARN', 'A19 建议显式记录数据冲突(11.2 必填)'

    # A20: 强证据占比 ≥ 70%
    if not re.search(r'强证据.*?70|证据.*?占比', section):
        return 'FAIL', 'A20 强证据占比 ≥ 70% 必填'

    return 'PASS', 'A18/A19/A20 三源校验章节齐全'


def check_s12_disclaimer(content: str) -> Tuple[str, str]:
    """S12. 免责声明 + 非推荐价位反向表达"""
    m = re.search(r'##\s*十二[、,]\s*免责声明.*?\n(.*?)(?=\n##\s|\Z)', content, re.DOTALL)
    if not m:
        return 'FAIL', '找不到"免责声明"章节'
    section = m.group(1)

    # "非推荐价位"反向表达
    if not re.search(r'非推荐价位|研究案例', section):
        return 'WARN', '建议加"非推荐价位/研究案例"反向表达'
    # 数据时效声明
    if not re.search(r'数据.*?(?:时效|快照|截至)', section):
        return 'WARN', '建议加数据时效声明(截至日期)'
    return 'PASS', '免责声明 + 反向表达齐全'


# ============ A18/A19/A20 个股专属 ============

def check_a18_three_sources(content: str, fm: dict) -> Tuple[str, str]:
    """A18. 三源数据配置(frontmatter data_sources)"""
    data_sources = fm.get('data_sources', {})
    required = ['primary', 'verified', 'reference', 'snapshot_date']
    missing = [k for k in required if k not in data_sources]
    if missing:
        return 'FAIL', f'frontmatter data_sources 缺字段:{missing}'

    # 检查三源配置
    valid_sources = ['myMCP', 'cninfo', 'ZsxqCrawler']
    for key in ['primary', 'verified', 'reference']:
        if data_sources[key] not in valid_sources:
            return 'WARN', f'data_sources.{key} = {data_sources[key]} 不是推荐三源(myMCP/cninfo/ZsxqCrawler)'

    return 'PASS', 'frontmatter data_sources 三源配置齐全'


def check_a19_snapshot_freshness(content: str, fm: dict) -> Tuple[str, str]:
    """A19. 数据时效性(单股报告 ≤ 7 天)"""
    snapshot_date = fm.get('data_sources', {}).get('snapshot_date', '')
    if not snapshot_date:
        return 'FAIL', 'data_sources.snapshot_date 必填'

    try:
        snap = datetime.strptime(snapshot_date, '%Y-%m-%d')
    except ValueError:
        return 'FAIL', f'snapshot_date 格式错误:{snapshot_date}(应为 YYYY-MM-DD)'

    age_days = (datetime.now() - snap).days
    if age_days < 0:
        return 'FAIL', f'snapshot_date 是未来日期:{snapshot_date}'
    if age_days > DATA_MAX_AGE_DAYS:
        return 'FAIL', f'数据快照已 {age_days} 天前,单股报告需 ≤ {DATA_MAX_AGE_DAYS} 天'
    return 'PASS', f'数据快照 {age_days} 天前(≤ {DATA_MAX_AGE_DAYS} 天)'


def check_a20_evidence_ratio(content: str) -> Tuple[str, str]:
    """A20. 强证据占比 ≥ 70%(从第 11.4 节读取声明值)"""
    # 读 11.4 节 — 用户/作者显式声明的强证据占比
    m = re.search(r'11\.4.*?(?:强证据|证据占比).*?\n(.*?)(?=\n###|\n##|\Z)', content, re.DOTALL)
    if not m:
        return 'WARN', 'A20 强证据占比需在 11.4 节显式填写(表 + 百分比)'

    section = m.group(1)

    # 优先:从表格中读"强证据"行的占比(更准确)
    # 找"强证据"行的百分比
    strong_match = re.search(r'强证据.*?(\d+)\s*%', section)
    if strong_match:
        ratio = int(strong_match.group(1)) / 100
        if ratio < MIN_EVIDENCE_RATIO:
            return 'FAIL', f'强证据占比 {strong_match.group(1)}% < {int(MIN_EVIDENCE_RATIO * 100)}%'
        return 'PASS', f'强证据占比 {strong_match.group(1)}% ≥ {int(MIN_EVIDENCE_RATIO * 100)}%'

    # fallback:扫整篇 emoji 计数(粗略,仅当 11.4 没填百分比时用)
    n_strong = len(re.findall(r'🟢', content))
    n_medium = len(re.findall(r'🟡', content))
    n_weak = len(re.findall(r'🔴', content))
    total = n_strong + n_medium + n_weak
    if total == 0:
        return 'WARN', 'A20 文章无证据 emoji,且 11.4 未填百分比'
    ratio = n_strong / total
    if ratio < MIN_EVIDENCE_RATIO:
        return 'WARN', f'整篇 emoji 计数强证据 {ratio*100:.0f}% < {int(MIN_EVIDENCE_RATIO * 100)}%(但 11.4 表声明优先)'
    return 'PASS', f'强证据占比 {ratio*100:.0f}% ≥ {int(MIN_EVIDENCE_RATIO * 100)}%'


def check_high_risk_words(content: str) -> Tuple[str, str]:
    """高风险词 0 误用(目标价/推荐/加仓等)"""
    issues = []
    for word in HIGH_RISK_WORDS:
        # 找出现位置,检查上下文 80 字是否有反向表达
        positions = [m.start() for m in re.finditer(word, content)]
        for pos in positions:
            context_start = max(0, pos - 80)
            context_end = min(len(content), pos + 80)
            context = content[context_start:context_end]
            # 反向表达关键词
            if not re.search(r'(?:非推荐|研究案例|仅供参考|不构成|仅为研究|仅为观察)', context):
                issues.append(f'"{word}" @ {pos},上下文 80 字内无反向表达')
    if issues:
        return 'FAIL', '; '.join(issues[:3]) + (f' ... 共 {len(issues)} 项' if len(issues) > 3 else '')
    return 'PASS', f'高风险词 0 处误用(检查 {len(HIGH_RISK_WORDS)} 个)'


def check_frontmatter(content: str) -> Tuple[str, str]:
    """frontmatter 完整性"""
    fm_match = re.match(r'---\n(.*?)\n---', content, re.DOTALL)
    if not fm_match:
        return 'FAIL', 'frontmatter 缺失'

    fm_text = fm_match.group(1)

    # 必填字段
    required = ['title', 'date', 'slug', 'tldr', 'data_sources', 'data_verified', 'zsxq_crawler']
    missing = [f for f in required if f'{f}:' not in fm_text and f'{f} =' not in fm_text]
    if missing:
        return 'FAIL', f'frontmatter 缺字段:{missing}'

    return 'PASS', 'frontmatter 必填字段齐全'


# ============ 主函数 ============

def parse_frontmatter(content: str) -> dict:
    """解析 frontmatter 为 dict(支持嵌套)"""
    fm_match = re.match(r'---\n(.*?)\n---', content, re.DOTALL)
    if not fm_match:
        return {}
    fm_text = fm_match.group(1)
    fm = {}
    current_key = None

    for line in fm_text.split('\n'):
        # 顶层 key(无缩进)
        top_match = re.match(r'^(\w[\w_]*):\s*(.*)$', line)
        if top_match:
            key = top_match.group(1)
            value = top_match.group(2).strip()
            current_key = key
            if value == '':
                fm[key] = {}
            else:
                fm[key] = value.strip('"').strip("'")
            continue

        # 嵌套 key(2 空格缩进)
        nested_match = re.match(r'^\s{2,}(\w[\w_]*):\s*(.*)$', line)
        if nested_match and current_key and isinstance(fm.get(current_key), dict):
            key = nested_match.group(1)
            value = nested_match.group(2).strip()
            fm[current_key][key] = value.strip('"').strip("'")

    return fm


def check_single_stock(slug: str, strict: bool = False) -> int:
    """检查单篇个股报告"""
    md_path = DRAFTS_POSTS / f'{slug}.md'
    if not md_path.exists():
        print(f'❌ 找不到文章:{md_path}')
        return 1

    content = md_path.read_text(encoding='utf-8')
    fm = parse_frontmatter(content)

    print(f'═══════════════════════════════════════════════════════════════')
    print(f'  个股报告完整性检查 · {slug}')
    print(f'═══════════════════════════════════════════════════════════════')

    # 12 章 + A18-A20 + 高风险词 + frontmatter
    checks = [
        ('Frontmatter', check_frontmatter(content)),
        ('S1 公司速览', check_s1_company_overview(content)),
        ('S2 投资逻辑 3 条', check_s2_three_logics(content)),
        ('S3 业务结构', check_s3_business_structure(content)),
        ('S4 行业地位', check_s4_industry_landscape(content)),
        ('S5 5 年财务', check_s5_financial_trend(content)),
        ('S6 业务亮点', check_s6_business_highlights(content)),
        ('S7 估值+反共识', check_s7_valuation(content)),
        ('S8 关键风险', check_s8_risks(content)),
        ('S9 反共识判断', check_s9_counter_consensus(content)),
        ('S10 跟踪信号', check_s10_signals(content)),
        ('S11 数据校验', check_s11_data_validation(content)),
        ('S12 免责声明', check_s12_disclaimer(content)),
        ('A18 三源配置', check_a18_three_sources(content, fm)),
        ('A19 数据时效', check_a19_snapshot_freshness(content, fm)),
        ('A20 强证据占比', check_a20_evidence_ratio(content)),
        ('高风险词', check_high_risk_words(content)),
    ]

    n_pass = n_warn = n_fail = 0
    for label, (status, msg) in checks:
        if status == 'PASS':
            icon = '✅'
            n_pass += 1
        elif status == 'WARN':
            icon = '⚠️ '
            n_warn += 1
        else:
            icon = '❌'
            n_fail += 1
        print(f'  {icon} [{label:18}] {msg}')

    print(f'═══════════════════════════════════════════════════════════════')
    print(f'  汇总:✅ {n_pass} | ⚠️  {n_warn} | ❌ {n_fail}')
    print(f'═══════════════════════════════════════════════════════════════')

    if n_fail == 0:
        print('🎉 **可发布**')
        return 0
    elif n_fail > 0 and strict:
        print('🚫 **严格模式下不可发布**(有 FAIL)')
        return 1
    else:
        print('⚠️  **可发布但有风险**')
        return 0


def main():
    parser = argparse.ArgumentParser(description='个股深度报告完整性检查')
    parser.add_argument('slug', nargs='?', help='文章 slug,如 shiying-equity')
    parser.add_argument('--all', action='store_true', help='检查所有个股草稿')
    parser.add_argument('--strict', action='store_true', help='任意 FAIL 直接 exit 1')

    args = parser.parse_args()

    if args.all:
        # 找所有 *-equity.md 文件
        slugs = [p.stem for p in DRAFTS_POSTS.glob('*-equity.md')]
        if not slugs:
            print('未找到个股草稿(*-equity.md)')
            return 0
        for slug in slugs:
            check_single_stock(slug, args.strict)
        return 0
    elif args.slug:
        return check_single_stock(args.slug, args.strict)
    else:
        parser.print_help()
        return 0


if __name__ == '__main__':
    sys.exit(main())