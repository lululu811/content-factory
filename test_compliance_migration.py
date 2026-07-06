#!/usr/bin/env python3
"""
测试 compliance 组件迁移
"""

import asyncio
from uuid import uuid4

from content_factory_core.models import Draft
from content_factory_sdk import discover_components


async def main():
    print("=" * 70)
    print("测试 1: 组件发现")
    print("=" * 70)

    registry = discover_components()
    components = registry.list_components()

    print(f"发现的组件:")
    for category, names in components.items():
        print(f"  {category}: {names}")

    if "default" not in components.get("compliance", []):
        print("✗ 未发现 compliance 组件")
        return

    print("✓ 发现 compliance 组件")

    print("\n" + "=" * 70)
    print("测试 2: 执行合规检查")
    print("=" * 70)

    provider = registry.get_compliance("default")
    if not provider:
        print("✗ 无法获取 compliance provider")
        return

    # 创建一个测试草稿
    draft = Draft(
        tenant_id=uuid4(),
        topic_id=uuid4(),
        editor_id=uuid4(),
        content="""# 稀土行业反共识真相：7 家公司真正受益

## 公司 5 分类

**北方稀土** (600111.SH)
**中国稀土** (000831.SZ)
**盛和资源** (600392.SH)
... (共 25 家公司)

## 配图

![稀土产业链](images/rare-earth-chain.png)
![供需分析](images/supply-demand.png)
![价格走势](images/price-trend.png)
![政策影响](images/policy-impact.png)
![投资建议](images/investment-advice.png)

## 免责声明

本文仅为研究案例，不构成投资建议。

""",
        metadata={"slug": "rare-earth-analysis"},
    )

    print(f"草稿内容预览 (前 100 字):")
    print(draft.content[:100] + "...")
    print()

    # 执行合规检查
    result = await provider.check(draft)

    print(f"检查结果:")
    print(f"  是否通过: {result['passed']}")
    print(f"  风险等级: {result['risk_level']}")
    print(f"  问题数: {len(result['issues'])}")
    print()

    if result["issues"]:
        print("问题详情:")
        for issue in result["issues"]:
            icon = {"PASS": "✅", "WARN": "⚠️ ", "FAIL": "❌", "ERROR": "💥"}[issue["status"]]
            print(f"  {icon} [{issue['code']}] {issue['name']}: {issue['message']}")

    # 完整结果对象
    full_result = result.get("result")
    if full_result:
        print(f"\n完整结果摘要: {full_result.summary()}")

    print("\n" + "=" * 70)
    print("✓ Compliance 组件迁移验证完成")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
