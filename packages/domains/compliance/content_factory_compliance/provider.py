"""
合规检查提供者

实现 ComplianceProvider SPI 接口，提供 17 项合规检查（含 17b）。
"""

import re
from datetime import date, datetime
from typing import Any

from content_factory_core.models import Article, Draft
from content_factory_sdk.spi import ComplianceProvider

from content_factory_compliance.models import CheckStatus, ComplianceCheck, ComplianceResult

# ── 常量定义 ──

HIGH_RISK_WORDS = ["目标价", "推荐", "保证", "加仓", "稳赚", "必涨", "必跌", "重仓", "满仓"]
MIN_COMPANIES_TOTAL = 20
MIN_TOP7 = 7
MIN_UPGRADE_SIGNALS = 3
MIN_DOWNGRADE_SIGNALS = 3
MIN_CONSENSUS_DIRECTIONS = 3
MIN_IMAGES = 5
MAX_TITLE_CHARS = 30

TICKER_PATTERNS = [
    r"\b\d{6}\.(?:SH|SZ)\b",
    r"\b\d{4,5}\.HK\b",
    r"\b\d{4}\.TW\b",
    r"\b[A-Z]{2,5}\.US\b",
    r"\b\d{6}\.SH\b|\b\d{6}\.SZ\b",
]


# ── 检查函数 ──


def check_1_title(content: str) -> tuple[CheckStatus, str]:
    """A1. 标题 ≤ 30 字 + 含反共识钩子"""
    m = re.search(r"^# (.+)$", content, re.MULTILINE)
    if not m:
        return CheckStatus.FAIL, "找不到一级标题"
    title = m.group(1).strip()
    if len(title) > MAX_TITLE_CHARS:
        return CheckStatus.FAIL, f"标题 {len(title)} 字,超过 30 字限制"
    hooks = [
        "反共识",
        "真实",
        "未必",
        "不是",
        "不在",
        "别再",
        "误区",
        "陷阱",
        "意外",
        "错位",
        "低估",
        "高估",
        "误读",
        "错判",
        "假的",
        "真的",
        "真相",
        "残酷",
        "清醒",
    ]
    if not any(h in title for h in hooks):
        return CheckStatus.WARN, "标题缺少反共识钩子关键词"
    return CheckStatus.PASS, f"标题 {len(title)} 字 + 含反共识钩子"


def check_2_companies_total(content: str) -> tuple[CheckStatus, str]:
    """A2. 候选公司 ≥ 20 个,5 分类齐全"""
    m = re.search(
        r"^##[^\n]*公司\s*5\s*分类[^\n]*\n(.*?)(?=^##\s)", content, re.DOTALL | re.MULTILINE
    )
    if not m:
        m = re.search(r"^##[^\n]*5\s*分类[^\n]*\n(.*?)(?=^##\s)", content, re.DOTALL | re.MULTILINE)
    if not m:
        return CheckStatus.FAIL, '找不到"公司 5 分类"章节'
    section = m.group(1)
    companies = re.findall(r"\*\*([^*\d]+?)\*\*", section)
    companies = [
        c
        for c in companies
        if c
        not in {
            "强证据",
            "中证据",
            "弱证据",
            "强",
            "中",
            "弱",
            "Controls",
            "Supplies",
            "Benefits",
            "Weak control",
            "Mainly has a story",
            "稀缺层",
        }
    ]
    unique = {c.strip() for c in companies if len(c.strip()) > 1}
    if len(unique) < MIN_COMPANIES_TOTAL:
        return CheckStatus.FAIL, f"候选公司 {len(unique)} 个,需 ≥ {MIN_COMPANIES_TOTAL}"
    return CheckStatus.PASS, f"候选公司 {len(unique)} 个"


def check_3_weak_story_have_tickers(content: str) -> tuple[CheckStatus, str]:
    """A3. 9.4 Weak / 9.5 Story 两类必须有具体股票代码"""
    weak_m = re.search(
        r"(?:###?\s*(?:7\.4|8\.4|9\.4|Has weak control))[^\n]*\n(.*?)(?=\n###?\s|\n##\s|\Z)",
        content,
        re.DOTALL | re.MULTILINE,
    )
    story_m = re.search(
        r"(?:###?\s*(?:7\.5|8\.5|9\.5|Mainly has a story))[^\n]*\n(.*?)(?=\n###?\s|\n##\s|\Z)",
        content,
        re.DOTALL | re.MULTILINE,
    )
    issues = []
    for label, mm in [("Weak", weak_m), ("Story", story_m)]:
        if not mm:
            issues.append(f"{label} 节缺失")
            continue
        section = mm.group(1)
        has_ticker = any(re.search(p, section) for p in TICKER_PATTERNS)
        has_placeholder = "..." in section
        company_mentions = re.findall(r"\*\*([^*\n]{2,15})\*\*", section)
        company_mentions = [c for c in company_mentions if not c.startswith(("强", "中", "弱"))]
        if has_placeholder:
            issues.append(f"{label} 节有 `...` 占位")
        if not has_ticker and not company_mentions:
            issues.append(f"{label} 节既无 ticker 也无具体公司名")
    if issues:
        return CheckStatus.FAIL, "; ".join(issues)
    return CheckStatus.PASS, "Weak + Story 两节有具体公司名 / ticker"


def check_4_top7(content: str) -> tuple[CheckStatus, str]:
    """A4. Top 7 完整 5 要素"""
    m = re.search(r"(?:##[^\n]*(?:Top\s*7|优先研究)[^\n]*\n)(.*?)(?=\n##\s|\Z)", content, re.DOTALL)
    if not m:
        return CheckStatus.FAIL, '找不到 "优先研究 Top 7" 章节'
    section = m.group(1)
    required_keys = ["卡住的环节", "产业链位置", "排序原因", "证据", "主要风险"]
    missing = [k for k in required_keys if k not in section]
    if missing:
        return CheckStatus.FAIL, f"Top 7 缺 5 要素: {missing}"
    candidates = re.findall(r"(?:[🥇🥈🥉]\s*)?#\s*(\d+)\b", section)
    if candidates:
        n = max(int(c) for c in candidates)
        if n < MIN_TOP7:
            return CheckStatus.WARN, f"Top 候选数 {n} < 7"
    return CheckStatus.PASS, "Top 7 完整 5 要素齐全"


def check_5_consensus(content: str) -> tuple[CheckStatus, str]:
    """A5. 反共识方向 ≥ 3 类"""
    m = re.search(r"##[^\n]*反共识[^\n]*\n(.*?)(?=\n##\s|\Z)", content, re.DOTALL)
    if not m:
        return CheckStatus.FAIL, '找不到"反共识判断"章节'
    section = m.group(1)
    n = len(re.findall(r"🔻", section))
    if n < MIN_CONSENSUS_DIRECTIONS:
        return CheckStatus.FAIL, f"反共识方向 {n} 类,需 ≥ {MIN_CONSENSUS_DIRECTIONS}"
    return CheckStatus.PASS, f"反共识方向 {n} 类"


def check_6_images(content: str) -> tuple[CheckStatus, str]:
    """A6. 配图 ≥ 5 张"""
    images = re.findall(r"!\[([^\]]*)\]\([^)]+\)", content)
    n = len(images)
    if n < MIN_IMAGES:
        return CheckStatus.FAIL, f"配图 {n} 张,需 ≥ {MIN_IMAGES}"
    return CheckStatus.PASS, f"配图 {n} 张"


def check_7_data_freshness(content: str) -> tuple[CheckStatus, str]:
    """A7. 数据时效 2026 H1 最新"""
    h1_2026 = len(re.findall(r"2026\s*H1", content))
    date_2026 = len(re.findall(r"2026[/\-]\d{1,2}", content))
    total = h1_2026 + date_2026
    if total < 3:
        return CheckStatus.WARN, f"2026 H1 / 日期标注 {total} 处,可能数据陈旧"
    return CheckStatus.PASS, f"2026 H1 数据标注 {total} 处"


def check_8_disclaimer(content: str) -> tuple[CheckStatus, str]:
    """B8. 免责声明"""
    if "免责声明" not in content:
        return CheckStatus.FAIL, '找不到"免责声明"标题'
    if "研究案例" not in content and "不构成推荐" not in content:
        return CheckStatus.WARN, "免责声明已加,但缺标注"
    return CheckStatus.PASS, "免责声明已加"


def check_9_evidence_levels(content: str) -> tuple[CheckStatus, str]:
    """B9. 证据等级 🟢🟡🔴 齐全"""
    has_green = "🟢" in content
    has_yellow = "🟡" in content
    has_red = "🔴" in content
    missing = []
    if not has_green:
        missing.append("🟢")
    if not has_yellow:
        missing.append("🟡")
    if not has_red:
        missing.append("🔴")
    if missing:
        return CheckStatus.WARN, f"证据等级缺: {' '.join(missing)}"
    return CheckStatus.PASS, "🟢🟡🔴 三档齐全"


def check_10_sources(content: str) -> tuple[CheckStatus, str]:
    """B10. 强结论有可查来源"""
    green_with_source = re.findall(
        r"🟢[^\n]*\[?[🟢L\d\d?]?[^\n]*?(?:报告|公告|财报|海关|监管|招股书|问询函|互动易|海关数据|ID|号)",
        content,
    )
    n = len(green_with_source)
    if n < 3:
        return CheckStatus.WARN, f"🟢 强证据来源标注 {n} 处,可能不够详细"
    return CheckStatus.PASS, f"🟢 强证据来源标注 {n} 处"


def check_11_high_risk_words(content: str) -> tuple[CheckStatus, str]:
    """B11. 高风险词 0 处误用"""
    issues = []
    for word in HIGH_RISK_WORDS:
        positions = [m.start() for m in re.finditer(re.escape(word), content)]
        for pos in positions:
            ctx = content[max(0, pos - 80) : min(len(content), pos + 80)]
            safe_patterns = ["不构成", "不推荐", "不代表", "非", "请勿", "仅为", "并非", "避免"]
            if not any(sp in ctx for sp in safe_patterns):
                issues.append(f'"{word}" 误用')
    if issues:
        return CheckStatus.FAIL, f"高风险词 {len(issues)} 处误用"
    return CheckStatus.PASS, "高风险词 0 处误用"


def check_12_time_window(content: str) -> tuple[CheckStatus, str]:
    """B12. 短期判断有时间窗口"""
    keywords = [
        "6 个月",
        "12 个月",
        "3-6 个月",
        "6-12 个月",
        "3 个月",
        "季度",
        "2026 H1",
        "2026 H2",
        "2026/Q1",
        "2026/Q2",
        "2026/Q3",
        "未来 6 个月",
        "未来 12 个月",
        "窗口",
    ]
    found = [k for k in keywords if k in content]
    if len(found) < 2:
        return CheckStatus.WARN, f"时间窗口标注 {len(found)} 处(< 2)"
    return CheckStatus.PASS, f"时间窗口标注 {len(found)} 处"


def check_13_signals(content: str) -> tuple[CheckStatus, str]:
    """B13. 升降级信号齐全(各 ≥ 3)"""
    up_m = re.search(
        r"(?:###?\s*(?:升级信号|α 兑现信号|alpha 兑现))[^\n]*\n(.*?)(?=\n###?\s|\n##\s|\Z)",
        content,
        re.DOTALL | re.MULTILINE,
    )
    down_m = re.search(
        r"(?:###?\s*(?:降级信号|判断需修正))[^\n]*\n(.*?)(?=\n###?\s|\n##\s|\Z)",
        content,
        re.DOTALL | re.MULTILINE,
    )
    up_count = len(re.findall(r"🟢", up_m.group(1))) if up_m else 0
    down_count = len(re.findall(r"🔴", down_m.group(1))) if down_m else 0
    issues = []
    if not up_m:
        issues.append('缺"升级信号"段落')
    elif up_count < MIN_UPGRADE_SIGNALS:
        issues.append(f"升级信号 {up_count} 条,< {MIN_UPGRADE_SIGNALS}")
    if not down_m:
        issues.append('缺"降级信号"段落')
    elif down_count < MIN_DOWNGRADE_SIGNALS:
        issues.append(f"降级信号 {down_count} 条,< {MIN_DOWNGRADE_SIGNALS}")
    if issues:
        return CheckStatus.FAIL, "; ".join(issues)
    return CheckStatus.PASS, f"升级 {up_count} 条 + 降级 {down_count} 条"


def check_14_tracking(content: str, slug: str) -> tuple[CheckStatus, str]:
    """B14. tracking/predictions/{slug}.json 已写入"""
    # 简化实现：总是返回 WARN，因为实际发布后才有
    return CheckStatus.WARN, "tracking 检查（发布后自动跑）"


def check_15_quote_citations(content: str) -> tuple[CheckStatus, str]:
    """C15. 访谈类文章必须有引用块"""
    if "interview:" not in content[:1000]:
        return CheckStatus.PASS, "非访谈类文章,跳过"
    en_blocks = len(re.findall(r"🇺🇸 \*\*\[EN\]\*\*", content))
    cn_blocks = len(re.findall(r"🇨🇳 \*\*\[CN\]\*\*", content))
    citation_lines = len(re.findall(r"^\s*> \*\*访谈引用", content, re.MULTILINE))
    issues = []
    if citation_lines < 10:
        issues.append(f"引用块仅 {citation_lines} 个,需 ≥ 10 个")
    if en_blocks != cn_blocks:
        issues.append(f"EN {en_blocks} 个 vs CN {cn_blocks} 个,不平衡")
    if issues:
        return CheckStatus.FAIL, "; ".join(issues)
    return CheckStatus.PASS, f"引用块 {citation_lines} 个"


def check_16_data_verified(content: str) -> tuple[CheckStatus, str]:
    """A16. 数据时效校验"""
    fm_match = re.match(r"---\n(.*?)\n---", content, re.DOTALL)
    if not fm_match:
        return CheckStatus.WARN, "未检测到 frontmatter 块"
    fm_text = fm_match.group(1)
    dv_match = re.search(r"data_verified:\n(.*?)(?=\n\S|\Z)", fm_text, re.DOTALL)
    if not dv_match:
        return CheckStatus.FAIL, "frontmatter 缺 data_verified 段"
    dv_text = dv_match.group(1)
    issues = []
    at_match = re.search(r'verified_at:\s*["\']?(\d{4}-\d{2}-\d{2})', dv_text)
    if not at_match:
        issues.append("verified_at 缺失")
    else:
        try:
            verified_date = datetime.strptime(at_match.group(1), "%Y-%m-%d").date()
            verified_age_days = (date.today() - verified_date).days
            if verified_age_days > 30:
                issues.append(f"verified_at 已过期 {verified_age_days} 天")
        except ValueError:
            issues.append("verified_at 解析失败")
    sources_match = re.search(r"verified_sources:\s*\n((?:[ \t]+-\s+.+\n)+)", dv_text)
    if not sources_match:
        issues.append("verified_sources 缺失")
    if issues:
        hard_keywords = ["已过期", "缺失", "解析失败"]
        hard_issues = [i for i in issues if any(k in i for k in hard_keywords)]
        status = CheckStatus.FAIL if hard_issues else CheckStatus.WARN
        return status, "; ".join(issues[:3])
    return CheckStatus.PASS, f"verified_at {at_match.group(1)}"


def check_17_research_reports(content: str) -> tuple[CheckStatus, str]:
    """A17. research_reports"""
    fm_match = re.match(r"---\n(.*?)\n---", content, re.DOTALL)
    if not fm_match:
        return CheckStatus.WARN, "未检测到 frontmatter 块"
    fm_text = fm_match.group(1)
    rr_match = re.search(r"research_reports:\n(.*?)(?=\n\S|\Z)", fm_text, re.DOTALL)
    if not rr_match:
        return CheckStatus.FAIL, "frontmatter 缺 research_reports 段"
    rr_text = rr_match.group(1)
    issues = []
    at_match = re.search(r'queried_at:\s*["\']?(\d{4}-\d{2}-\d{2})', rr_text)
    if not at_match:
        issues.append("queried_at 缺失")
    found_concepts_count = len(re.findall(r"-\s+name:", rr_text))
    if found_concepts_count == 0:
        issues.append("linked_concepts 为空")
    if issues:
        return CheckStatus.WARN, "; ".join(issues[:3])
    return CheckStatus.PASS, f"research_reports {found_concepts_count} 个概念"


def check_17b_zsxq_crawler(content: str) -> tuple[CheckStatus, str]:
    """A17b. ZsxqCrawler 原始导出"""
    fm_match = re.match(r"---\n(.*?)\n---", content, re.DOTALL)
    if not fm_match:
        return CheckStatus.FAIL, "未检测到 frontmatter 块"
    fm_text = fm_match.group(1)
    zc_match = re.search(r"zsxq_crawler:\n(.*?)(?=\n\S|\Z)", fm_text, re.DOTALL)
    if not zc_match:
        return CheckStatus.FAIL, "frontmatter 缺 zsxq_crawler 段"
    zc_text = zc_match.group(1)
    issues = []
    at_match = re.search(r'queried_at:\s*["\']?(\d{4}-\d{2}-\d{2})', zc_text)
    if not at_match:
        issues.append("queried_at 缺失")
    else:
        try:
            queried_date = datetime.strptime(at_match.group(1), "%Y-%m-%d").date()
            queried_age_days = (date.today() - queried_date).days
            if queried_age_days > 30:
                issues.append(f"queried_at 已过期 {queried_age_days} 天")
        except ValueError:
            issues.append("queried_at 解析失败")
    cs_match = re.search(r"cited_sections:\s*(\d+)", zc_text)
    cited_sections = int(cs_match.group(1)) if cs_match else 0
    if cited_sections < 1:
        issues.append(f"cited_sections = {cited_sections}")
    citations_count = len(re.findall(r"-\s+file:", zc_text))
    if citations_count < 1:
        issues.append(f"citations = {citations_count} 项")
    if issues:
        hard_keywords = ["缺失", "已过期", "cited_sections = 0", "citations = 0"]
        hard_issues = [i for i in issues if any(k in i for k in hard_keywords)]
        status = CheckStatus.FAIL if hard_issues else CheckStatus.WARN
        return status, "; ".join(issues[:3])
    return CheckStatus.PASS, f"zsxq_crawler {cited_sections} 节 {citations_count} 引用"


# ── Provider 实现 ──


class DefaultComplianceProvider(ComplianceProvider):
    """默认合规检查提供者"""

    async def check(self, draft: Draft) -> dict[str, Any]:
        """检查草稿是否合规"""
        content = draft.content
        slug = draft.metadata.get("slug", "unknown")
        checks: list[ComplianceCheck] = []

        # 执行 17 项检查（含 17b）
        check_functions = [
            ("A1", "标题长度与钩子", lambda c: check_1_title(c)),
            ("A2", "候选公司数量", lambda c: check_2_companies_total(c)),
            ("A3", "Weak/Story 有 ticker", lambda c: check_3_weak_story_have_tickers(c)),
            ("A4", "Top 7 完整", lambda c: check_4_top7(c)),
            ("A5", "反共识方向", lambda c: check_5_consensus(c)),
            ("A6", "配图数量", lambda c: check_6_images(c)),
            ("A7", "数据时效", lambda c: check_7_data_freshness(c)),
            ("B8", "免责声明", lambda c: check_8_disclaimer(c)),
            ("B9", "证据等级", lambda c: check_9_evidence_levels(c)),
            ("B10", "强结论来源", lambda c: check_10_sources(c)),
            ("B11", "高风险词", lambda c: check_11_high_risk_words(c)),
            ("B12", "时间窗口", lambda c: check_12_time_window(c)),
            ("B13", "升降级信号", lambda c: check_13_signals(c)),
            ("B14", "tracking 记录", lambda c: check_14_tracking(c, slug)),
            ("C15", "访谈引用", lambda c: check_15_quote_citations(c)),
            ("A16", "数据校验", lambda c: check_16_data_verified(c)),
            ("A17", "research_reports", lambda c: check_17_research_reports(c)),
            ("A17b", "ZsxqCrawler", lambda c: check_17b_zsxq_crawler(c)),
        ]

        for code, name, func in check_functions:
            try:
                status, message = func(content)
                checks.append(ComplianceCheck(code=code, name=name, status=status, message=message))
            except Exception as e:
                checks.append(
                    ComplianceCheck(
                        code=code, name=name, status=CheckStatus.ERROR, message=f"检查异常: {e}"
                    )
                )

        # 构建结果
        result = ComplianceResult(
            draft_id=draft.id,
            article_slug=slug,
            checks=checks,
        )

        return {
            "passed": result.can_publish,
            "issues": [
                {"code": c.code, "name": c.name, "status": c.status.value, "message": c.message}
                for c in checks
                if c.status != CheckStatus.PASS
            ],
            "risk_level": "high"
            if result.has_failures
            else ("medium" if result.warned_count > 0 else "low"),
            "result": result,
            "summary": {
                "total": len(checks),
                "passed": result.passed_count,
                "warned": result.warned_count,
                "failed": result.failed_count,
                "error": result.error_count,
            },
        }

    async def approve(self, draft: Draft) -> Article:
        """批准草稿，生成终稿"""
        return Article(
            tenant_id=draft.tenant_id,
            topic_id=draft.topic_id,
            editor_id=draft.editor_id,
            draft_id=draft.id,
            title=draft.metadata.get("title", "未命名文章"),
            content=draft.content,
            metadata={**draft.metadata, "approved_at": "2026-07-07T00:00:00"},
        )
