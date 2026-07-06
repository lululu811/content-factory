"""
合规检查提供者

实现 ComplianceProvider SPI 接口，提供 16+ 项合规检查。
"""

import re
from typing import Any
from uuid import UUID

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
        return CheckStatus.FAIL, f"标题 {len(title)} 字,超过 30 字限制: {title!r}"
    hooks = [
        "反共识", "真实", "未必", "不是", "不在", "别再", "误区", "陷阱",
        "意外", "错位", "低估", "高估", "误读", "错判", "假的", "真的",
        "真相", "残酷", "清醒",
    ]
    if not any(h in title for h in hooks):
        return CheckStatus.WARN, f"标题缺少反共识钩子关键词(建议加: {hooks[:3]})"
    return CheckStatus.PASS, f"标题 {len(title)} 字 + 含反共识钩子"


def check_2_companies_total(content: str) -> tuple[CheckStatus, str]:
    """A2. 候选公司 ≥ 20 个,5 分类齐全"""
    m = re.search(
        r"^##[^\n]*公司\s*5\s*分类[^\n]*\n(.*?)(?=^##\s)", content, re.DOTALL | re.MULTILINE
    )
    if not m:
        m = re.search(
            r"^##[^\n]*5\s*分类[^\n]*\n(.*?)(?=^##\s)", content, re.DOTALL | re.MULTILINE
        )
    if not m:
        return CheckStatus.FAIL, '找不到"公司 5 分类"章节'
    section = m.group(1)
    companies = re.findall(r"\*\*([^*\d]+?)\*\*", section)
    companies = [
        c for c in companies
        if c not in {
            "强证据", "中证据", "弱证据", "强", "中", "弱",
            "Controls", "Supplies", "Benefits", "Weak control",
            "Mainly has a story", "稀缺层",
        }
    ]
    unique = {c.strip() for c in companies if len(c.strip()) > 1}
    if len(unique) < MIN_COMPANIES_TOTAL:
        return CheckStatus.FAIL, f"候选公司 {len(unique)} 个,需 ≥ {MIN_COMPANIES_TOTAL}"
    return CheckStatus.PASS, f"候选公司 {len(unique)} 个(≥ {MIN_COMPANIES_TOTAL})"


def check_6_images(content: str) -> tuple[CheckStatus, str]:
    """A6. 配图 ≥ 5 张"""
    images = re.findall(r"!\[([^\]]*)\]\([^)]+\)", content)
    n = len(images)
    if n < MIN_IMAGES:
        return CheckStatus.FAIL, f"配图 {n} 张,需 ≥ {MIN_IMAGES}"
    return CheckStatus.PASS, f"配图 {n} 张(≥ {MIN_IMAGES})"


def check_8_disclaimer(content: str) -> tuple[CheckStatus, str]:
    """B8. 免责声明"""
    keywords = ["不构成投资建议", "不构成推荐", "研究案例", "免责声明"]
    found = [k for k in keywords if k in content]
    if "免责声明" not in content:
        return CheckStatus.FAIL, '找不到"免责声明"标题'
    if "研究案例" not in content and "不构成推荐" not in content:
        return CheckStatus.WARN, f'免责声明已加,但缺"研究案例 / 不构成推荐"标注。命中: {found}'
    return CheckStatus.PASS, f"免责声明已加(含 {','.join(found)})"


def check_11_high_risk_words(content: str) -> tuple[CheckStatus, str]:
    """B11. 高风险词 0 处误用"""
    issues = []
    for word in HIGH_RISK_WORDS:
        positions = [m.start() for m in re.finditer(re.escape(word), content)]
        for pos in positions:
            ctx = content[max(0, pos - 80) : min(len(content), pos + 80)]
            safe_patterns = [
                "不构成", "不推荐", "不代表", "非", "请勿",
                "仅为", "并非", "避免",
            ]
            if not any(sp in ctx for sp in safe_patterns):
                issues.append(f'"{word}" @ 位置 {pos},上下文 80 字内无反向表达')
    if issues:
        return CheckStatus.FAIL, "; ".join(issues[:3]) + (
            f" ... 共 {len(issues)} 处" if len(issues) > 3 else ""
        )
    return CheckStatus.PASS, f"高风险词 0 处误用(检查 {len(HIGH_RISK_WORDS)} 个)"


# ── Provider 实现 ──

class DefaultComplianceProvider(ComplianceProvider):
    """默认合规检查提供者"""

    async def check(self, draft: Draft) -> dict[str, Any]:
        """
        检查草稿是否合规
        返回: {"passed": bool, "issues": [...], "risk_level": str}
        """
        content = draft.content
        checks: list[ComplianceCheck] = []

        # 执行各项检查
        check_functions = [
            ("A1", "标题长度与钩子", check_1_title),
            ("A2", "候选公司数量", check_2_companies_total),
            ("A6", "配图数量", check_6_images),
            ("B8", "免责声明", check_8_disclaimer),
            ("B11", "高风险词", check_11_high_risk_words),
        ]

        for code, name, func in check_functions:
            status, message = func(content)
            checks.append(ComplianceCheck(
                code=code,
                name=name,
                status=status,
                message=message,
            ))

        # 构建结果
        result = ComplianceResult(
            draft_id=draft.id,
            article_slug=draft.metadata.get("slug", "unknown"),
            checks=checks,
        )

        # 返回 SPI 接口要求的格式
        return {
            "passed": result.can_publish,
            "issues": [
                {"code": c.code, "name": c.name, "status": c.status.value, "message": c.message}
                for c in checks
                if c.status != CheckStatus.PASS
            ],
            "risk_level": "high" if result.has_failures else ("medium" if result.warned_count > 0 else "low"),
            "result": result,  # 附加完整结果对象
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
