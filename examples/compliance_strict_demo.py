#!/usr/bin/env python3
"""
content-factory 合规检查阻断演示

构造一篇故意缺关键 frontmatter 字段(数据时效、来源、合规免责)的草稿,
展示 18 项合规检查如何 FAIL → publish --strict 阻断。

用法:
    uv run python examples/compliance_strict_demo.py
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


async def main() -> None:
    from uuid import uuid4

    from content_factory_core.models import Draft
    from content_factory_core.tenant_manager import get_tenant_manager
    from content_factory_compliance import DefaultComplianceProvider

    print("🚦 content-factory 合规阻断演示")
    print("=" * 50)

    # 1. 故意构造一篇**不合规**的草稿(empty content + empty metadata)
    tenant_mgr = get_tenant_manager()
    tenant = tenant_mgr.create_tenant(name="Demo Team", slug="compliance-demo")
    bad_draft = Draft(
        tenant_id=tenant.id,
        topic_id=uuid4(),
        editor_id=uuid4(),
        content="无免责声明、无数据来源、无证据等级的草稿。",  # noqa
        metadata={},  # 故意全空,触发多个 FAIL
    )

    print("\n[1/2] 故意构造不合规草稿:")
    print(f"  - 正文长度:{len(bad_draft.content)} 字")
    print(f"  - metadata 字段:0 个")

    # 2. 跑合规检查
    compliance = DefaultComplianceProvider()
    result = await compliance.check(bad_draft)

    print("\n[2/2] 合规检查结果:")
    print(f"  {'✅ PASS' if result['passed'] else '❌ FAIL'} (risk_level={result['risk_level']})")
    print(f"  issues 总数:{len(result['issues'])}")

    by_status: dict[str, list] = {"PASS": [], "WARN": [], "FAIL": [], "ERROR": []}
    for issue in result["issues"]:
        by_status.setdefault(issue.get("status", "INFO"), []).append(issue)

    for status in ("FAIL", "WARN", "PASS", "ERROR"):
        items = by_status.get(status, [])
        if items:
            print(f"\n  [{status}] {len(items)} 项:")
            for it in items[:8]:
                msg = it.get("message", "")
                print(f"    {it['code']:>5s} | {msg[:80]}")
            if len(items) > 8:
                print(f"    ...({len(items) - 8} more)")

    # 3. 演示 --strict 阻断
    print("\n" + "=" * 50)
    if not result["passed"]:
        print("❌ 按设计 publish --strict 会阻断,这是合规门禁的正常行为。")
        print("   修复方式:补全 frontmatter + 加免责声明 + 引用数据源 → 重跑 compliance。")
    else:
        print("⚠️  这篇竟然过了 compliance——可能是检查规则太松,需要 review。")


if __name__ == "__main__":
    asyncio.run(main())
