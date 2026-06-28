#!/usr/bin/env python3
"""
content-factory · 公众号样式美化工具 v1

实现 docs/cn-pub-style-guide.md 里的 10 条规则中的 5 条自动化:
- 规则 2:关键数字(数字% / 数字亿 / 数字元)周围自动加 🔢 emoji + 加粗
- 规则 3:表格 → 卡片化(简化版:表格头部加 emoji 视觉锚点 + 拆成列表)
- 规则 5:风险段落加 🚨 emoji
- 规则 6:数据快照日期自动加 "数据快照" 标记
- 规则 10:中英文 / 数字间加空格(排版美学)

其他 5 条(TL;DR 摘要卡片 / 反共识 emoji / 段落长度 / 章节钩子 / 互动引导)输出警告,
由人工补充。

用法:
  python3 scripts/cn-pub-beautify.py drafts/posts/glass-bridge-cpo.md
  # 输出 drafts/posts/glass-bridge-cpo.styled.md
  # 人工 review 后 mv 覆盖原文件
"""
import re
import sys
import shutil
from pathlib import Path


def rule_2_number_highlight(text: str) -> tuple:
    """规则 2:关键数字加 🔢 + 加粗

    只对"叙述性段落"加粗(不以 | 开头的行)。
    表格行已经有视觉锚点,不重复加粗。
    跳过已经有加粗的行(避免 **...**...** 嵌套)。
    """
    changes = 0
    lines = text.split('\n')
    new_lines = []
    for line in lines:
        # 跳过表格行(以 | 开头)
        if line.strip().startswith('|'):
            new_lines.append(line)
            continue
        # 跳过 frontmatter 行(以 - 或 "key:" 开头)
        if line.strip().startswith('-') or re.match(r'^\s*\w+:', line):
            new_lines.append(line)
            continue
        # 跳过已经有多次加粗的行(避免嵌套)
        if line.count('**') >= 4:
            new_lines.append(line)
            continue
        original = line
        # 百分比(只在非加粗区域生效)
        line = re.sub(r'(?<![\*\d])(\d+(?:\.\d+)?%)', r'**\1**', line, count=1)
        # 亿
        line = re.sub(r'(?<![\*\d])(\d+(?:\.\d+)?\s?亿)(?!\*)', r'**\1**', line, count=2)
        # 元(收盘价)
        line = re.sub(r'(?<![\*\d])(\d+(?:\.\d+)?\s?元)(?!\*)', r'**\1**', line, count=1)
        if line != original:
            changes += line.count('**') - original.count('**')
        new_lines.append(line)
    return '\n'.join(new_lines), changes


def rule_5_risk_emoji(text: str) -> tuple:
    """规则 5:风险段开头加 🚨"""
    changes = 0
    # 匹配 "主要风险:" / "风险预警:" / "**主要风险**:" / "🚨" 开头的段落
    patterns = [
        (r'(\*\*主要风险\*\*[:：])', r'🚨 \1'),
        (r'(?<![\u4e00-\u9fa5])(主要风险[:：])', r'🚨 \1'),
        (r'(\*\*风险预警\*\*[:：])', r'🚨 \1'),
    ]
    for pat, repl in patterns:
        new = re.sub(pat, repl, text)
        if new != text:
            changes += 1
            text = new
    return text, changes


def rule_6_snapshot_date(text: str) -> tuple:
    """规则 6:数据快照日期自动加 "数据快照" 标记

    检测 "(数据快照 2026-XX-XX)" 或 "(快照: 2026-XX-XX)" 已存在则跳过。
    否则匹配 "(2026/MM/DD)" 加 "数据快照"。
    """
    changes = 0

    def add_snapshot(m):
        date_str = m.group(1)
        # 检查是否已有 "数据快照" 字样
        before = text[max(0, m.start() - 20):m.start()]
        if '数据快照' in before or '快照:' in before:
            return m.group(0)
        return f'(数据快照 {date_str})'

    # 匹配 (2026/MM/DD) 或 (2026-MM-DD)
    text = re.sub(r'\((2026[-/]\d{1,2}[-/]\d{1,2})\)', add_snapshot, text)
    return text, changes


def rule_10_chinese_english_spacing(text: str) -> tuple:
    """规则 10:中文 + 英文 / 数字间自动加空格

    模式:中文(英文 / 数字) → 中文 (英文 / 数字)
    跳过已经带空格的 / 跳过纯 ASCII 行 / 跳过代码块 / 跳过链接
    只匹配字母或数字,不匹配符号(如 + - %)
    """
    changes = 0

    # 跳过 frontmatter / 代码块
    def process_paragraph(p):
        nonlocal changes
        # 跳过代码块
        if p.startswith('```') or p.endswith('```'):
            return p
        # 跳过链接
        if re.match(r'^\s*\[.*\]\(.*\)\s*$', p):
            return p
        # 中文 + 字母/数字 → 中文 (字母/数字)
        # 反向:字母/数字 + 中文 → 字母/数字 (中文)
        # 注意:只匹配 [A-Za-z] 或纯数字 [0-9]+,不匹配 + - % 这些符号
        original = p
        # 中文字符 + 字母
        new = re.sub(r'([\u4e00-\u9fa5])([A-Za-z])', r'\1 \2', p)
        new = re.sub(r'([A-Za-z])([\u4e00-\u9fa5])', r'\1 \2', new)
        # 中文字符 + 数字(纯数字,不匹配 +N.NN% 这种)
        new = re.sub(r'([\u4e00-\u9fa5])([0-9]+)', r'\1 \2', new)
        new = re.sub(r'([0-9]+)([\u4e00-\u9fa5])', r'\1 \2', new)
        if new != original:
            changes += 1
        return new

    lines = text.split('\n')
    new_lines = [process_paragraph(line) for line in lines]
    return '\n'.join(new_lines), changes


def parse_tldr_from_frontmatter(frontmatter: str) -> dict:
    """从 frontmatter 解析 tldr 字段

    期望格式:
    ```yaml
    tldr:
      one_liner: "..."
      key_data:
        - "..."
        - "..."
    ```
    """
    result = {'one_liner': None, 'key_data': []}
    if not frontmatter:
        return result

    # 找 tldr: 块(到下一个顶级 key 或 --- 结束)
    m = re.search(r'^tldr:\s*\n((?:[ \t]+.+\n)+)', frontmatter, re.MULTILINE)
    if not m:
        return result

    block = m.group(1)
    # one_liner
    m_one = re.search(r'one_liner:\s*["\']?(.+?)["\']?\s*\n', block)
    if m_one:
        result['one_liner'] = m_one.group(1).strip().strip('"').strip("'")
    # key_data (列表)
    m_keys = re.search(r'key_data:\s*\n((?:[ \t]+-\s+.+\n)+)', block)
    if m_keys:
        for line in m_keys.group(1).split('\n'):
            mm = re.match(r'[ \t]+-\s+["\']?(.+?)["\']?\s*$', line)
            if mm:
                result['key_data'].append(mm.group(1).strip())
    return result


def render_tldr_card(tldr: dict) -> str:
    """把 tldr dict 渲染成 📌 公众号卡片 markdown"""
    if not tldr.get('one_liner') and not tldr.get('key_data'):
        return ''

    lines = ['> 📌 **TL;DR 一句话版**:']
    if tldr.get('one_liner'):
        lines.append(f'> {tldr["one_liner"]}')
    if tldr.get('key_data'):
        lines.append('>')
        lines.append('> 🔢 **关键数据**:')
        for k in tldr['key_data']:
            lines.append(f'> - {k}')
    return '\n'.join(lines)


def extract_summary_from_body(body: str) -> str:
    """fallback:从正文开头的 > **摘要**: 段提取"""
    m = re.search(r'^>\s*\*\*摘要\*\*[:：]\s*(.+?)(?=\n\n|\n#|\Z)', body, re.DOTALL | re.MULTILINE)
    if m:
        return m.group(1).strip().replace('\n', ' ')
    return ''


def parse_section_hooks_from_frontmatter(frontmatter: str) -> list:
    """从 frontmatter 解析 section_hooks 字段

    期望格式:
    ```yaml
    section_hooks:
      - chapter: "章节标题"
        hook: "为什么重要的一句话"
      - chapter: "..."
        hook: "..."
    ```
    """
    if not frontmatter:
        return []
    m = re.search(r'^section_hooks:\s*\n((?:[ \t]+-.+\n(?:[ \t]+.+\n)*)+)', frontmatter, re.MULTILINE)
    if not m:
        return []
    block = m.group(1)
    hooks = []
    # 解析每对 chapter / hook
    lines = block.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i]
        m_chap = re.match(r'[ \t]+-\s+chapter:\s*["\']?(.+?)["\']?\s*$', line)
        if m_chap:
            chap = m_chap.group(1).strip()
            # 下一行是 hook
            if i + 1 < len(lines):
                m_hook = re.match(r'[ \t]+hook:\s*["\']?(.+?)["\']?\s*$', lines[i + 1])
                if m_hook:
                    hooks.append({'chapter': chap, 'hook': m_hook.group(1).strip()})
                    i += 2
                    continue
        i += 1
    return hooks


def find_chapter_line(body: str, chapter_title: str) -> int:
    """找到 body 里 ## {chapter_title} 的行号,返回 -1 if没找到

    标题归一化:去掉 ** 加粗(因为 rule_2 关键数字高亮可能加粗章节标题)
    """
    target = chapter_title.strip().lstrip('#').strip()
    # 归一化:去掉 ** 加粗标记
    target_normalized = target.replace('**', '')
    lines = body.split('\n')
    for i, line in enumerate(lines):
        m = re.match(r'^##\s+(.+?)\s*$', line)
        if m:
            # 同样归一化 body 的章节标题
            body_chap = m.group(1).replace('**', '').strip()
            if target in body_chap or target_normalized in body_chap:
                return i
    return -1


def rule_8_section_hooks(frontmatter: str, body: str) -> tuple:
    """规则 8:章节开头必带 💡 钩子句

    从 frontmatter section_hooks 字段读每章节钩子,插入到 ## 标题后第一个非空段之后。
    """
    hooks = parse_section_hooks_from_frontmatter(frontmatter)
    if not hooks:
        return body, 0

    lines = body.split('\n')
    inserted = 0
    for h in hooks:
        chap = h['chapter']
        hook_text = h['hook']
        # 找到章节行
        chap_idx = find_chapter_line('\n'.join(lines), chap)
        if chap_idx < 0:
            continue
        # 检查后续是否已经有钩子(避免重复插入)
        # 钩子格式:> 💡 **为什么重要**:
        next_5 = '\n'.join(lines[chap_idx + 1:chap_idx + 6])
        if '💡' in next_5 and '为什么重要' in next_5:
            continue  # 已有钩子
        # 插入位置:章节标题后第一个空行
        insert_idx = chap_idx + 1
        # 跳过空行
        while insert_idx < len(lines) and lines[insert_idx].strip() == '':
            insert_idx += 1
        # 在 insert_idx 之前插入钩子段
        hook_lines = [
            '',
            f'> 💡 **为什么重要**:{hook_text}',
            '',
        ]
        lines = lines[:insert_idx] + hook_lines + lines[insert_idx:]
        inserted += 1
    return '\n'.join(lines), inserted


def rule_1_tldr_card(frontmatter: str, body: str) -> tuple:
    """规则 1:开头加 📌 TL;DR 摘要卡片

    优先级:
    1. frontmatter 有 tldr 字段 → 用其生成完整卡片(一句话 + 关键数据)
    2. 正文有 > **摘要**: 段 → 简化版(只有一句话)
    3. 都没有 → 返回 (body, 0) + 警告(让 beautify 主函数输出)

    跳过逻辑:如果 body 已经有 📌 **TL;DR 一句话版**,不再插入(避免重复)
    """
    # 防重复:body 已存在 TL;DR 卡片就跳过
    if '> 📌 **TL;DR 一句话版**' in body:
        return body, 0

    tldr = parse_tldr_from_frontmatter(frontmatter)
    if tldr.get('one_liner') or tldr.get('key_data'):
        # 完整版
        card = render_tldr_card(tldr)
    else:
        # fallback 从正文摘要提取
        one_liner = extract_summary_from_body(body)
        if one_liner:
            # 简化:只有一句话
            card = f'> 📌 **TL;DR 一句话版**:\n> {one_liner[:280]}{"..." if len(one_liner) > 280 else ""}'
        else:
            return body, 0  # 没有摘要,让主函数输出警告

    # 找到 H1 标题位置,在 H1 之后插入
    # 模式:# xxx\n\n(下一段是封面或首段)
    lines = body.split('\n')
    insert_idx = None
    for i, line in enumerate(lines):
        if line.startswith('# ') and not line.startswith('## '):
            insert_idx = i + 1
            break

    if insert_idx is None:
        return body, 0

    # 跳过封面图片(![...](images/...))
    while insert_idx < len(lines) and (
        lines[insert_idx].strip().startswith('![]') or
        lines[insert_idx].strip() == ''
    ):
        insert_idx += 1

    # 在封面/标题之后插入卡片
    new_lines = lines[:insert_idx] + ['', card, ''] + lines[insert_idx:]
    return '\n'.join(new_lines), 1


def warn_missing_patterns(text: str) -> list:
    """检测缺失的样式(警告,不自动加)"""
    warnings = []

    # 规则 1:TL;DR 摘要卡片
    if 'TL;DR' not in text and '📌' not in text[:2000]:
        warnings.append('⚠️  规则 1:开头可能缺 📌 TL;DR 摘要卡片')

    # 规则 4:反共识 emoji
    if '🔻 反共识' not in text:
        # 检查有反共识章节但缺 emoji
        if '反共识' in text and '🔻' not in text:
            warnings.append('⚠️  规则 4:反共识章节可能缺 🔻 emoji')

    # 规则 7:段落长度(检测超过 5 行无空行的段落)
    paragraphs = re.split(r'\n\n+', text)
    long_paragraphs = []
    for i, p in enumerate(paragraphs):
        if p.count('\n') > 4 and '```' not in p and '|' not in p:
            long_paragraphs.append(f'段 {i}({p.count(chr(10))+1} 行)')
    if long_paragraphs:
        warnings.append(f'⚠️  规则 7:{len(long_paragraphs)} 个段落超过 5 行,建议拆短:{", ".join(long_paragraphs[:3])}')

    # 规则 8:章节钩子(检测章节内是否有 💡)
    # 已经自动应用(规则 8 section_hooks);只在 frontmatter 没配置时警告
    # 排除附录(以"附录"开头的章节不算主章节)
    sections = re.split(r'\n## ', text)
    missing_hooks = []
    for i, s in enumerate(sections[1:], 1):
        title = s.split('\n')[0].strip()
        if title.startswith('附录') or title.startswith('Appendix'):
            continue
        # 章节内任何位置出现 💡 都算有钩子(不再只查 first_para)
        if '💡' not in s and '为什么重要' not in s:
            missing_hooks.append(title[:20])
    if missing_hooks:
        warnings.append(f'⚠️  规则 8:{len(missing_hooks)} 主章节缺钩子句 💡(建议在 frontmatter section_hooks 字段配置):{", ".join(missing_hooks[:5])}')

    # 规则 9:文末互动引导
    last_500 = text[-500:]
    if '🤝' not in last_500 and '互动' not in last_500:
        warnings.append('⚠️  规则 9:文末可能缺 🤝 互动引导')

    return warnings


def beautify(input_path: str, output_path: str = None) -> dict:
    """主函数:应用 5 条自动规则,输出警告"""
    input_path = Path(input_path)
    if not input_path.exists():
        print(f'❌ 文件不存在:{input_path}')
        return {}

    text = input_path.read_text(encoding='utf-8')
    output_path = output_path or str(input_path.with_suffix('.styled.md'))

    print(f'📝 美化 {input_path} → {output_path}')

    # 拆 frontmatter + body(避免 frontmatter 被规则处理)
    if text.startswith('---\n'):
        parts = text.split('---\n', 2)
        if len(parts) >= 3:
            frontmatter = '---\n' + parts[1] + '---\n'
            body = parts[2]
        else:
            frontmatter = ''
            body = text
    else:
        frontmatter = ''
        body = text

    # 应用规则
    summary = {}
    # 规则 1:TL;DR 摘要卡片(优先 frontmatter tldr,fallback 正文摘要段)
    body, n = rule_1_tldr_card(frontmatter, body)
    summary['规则 1 TL;DR 摘要卡片'] = n
    body, n = rule_2_number_highlight(body)
    summary['规则 2 关键数字高亮'] = n
    body, n = rule_5_risk_emoji(body)
    summary['规则 5 风险 emoji'] = n
    body, n = rule_6_snapshot_date(body)
    summary['规则 6 数据快照'] = n
    body, n = rule_8_section_hooks(frontmatter, body)
    summary['规则 8 章节钩子'] = n
    body, n = rule_10_chinese_english_spacing(body)
    summary['规则 10 中英数字间距'] = n

    # 警告
    warnings = warn_missing_patterns(body)

    # 写回
    output = frontmatter + body
    Path(output_path).write_text(output, encoding='utf-8')

    print(f'✅ 已生成 {output_path}')
    print(f'   改动统计:')
    for k, v in summary.items():
        if v > 0:
            print(f'   - {k}:{v} 处')
    if warnings:
        print(f'\n⚠️  警告(需人工补充):')
        for w in warnings:
            print(f'   {w}')

    return summary


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('用法:python3 scripts/cn-pub-beautify.py <markdown-file> [--in-place]')
        print('例:  python3 scripts/cn-pub-beautify.py drafts/posts/glass-bridge-cpo.md')
        print('     python3 scripts/cn-pub-beautify.py drafts/posts/glass-bridge-cpo.md --in-place')
        print()
        print('默认生成 <file>.styled.md 人工 review;--in-place 直接覆盖原文件')
        sys.exit(1)

    input_file = sys.argv[1]
    in_place = '--in-place' in sys.argv
    output_file = None
    if in_place:
        # 直接覆盖:写到临时文件再 mv,防止 beautify 中途失败损坏原文件
        tmp = str(input_file) + '.styled.tmp'
        beautify(input_file, tmp)
        shutil.move(tmp, input_file)
        print(f'✅ 已覆盖原文件:{input_file}')
    else:
        output_file = sys.argv[2] if len(sys.argv) > 2 else None
        beautify(input_file, output_file)