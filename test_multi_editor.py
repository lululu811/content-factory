#!/usr/bin/env python3
"""
测试多编辑风格：严肃派 vs 犀利派
"""

import asyncio
from uuid import uuid4

from content_factory_core.models import RunContext, Topic
from content_factory_sdk import discover_components


async def main():
    print("=" * 70)
    print("测试多编辑风格：严肃派 vs 犀利派")
    print("=" * 70)

    registry = discover_components()
    components = registry.list_components()
    print(f"\n发现的编辑: {components['editors']}")

    # 创建测试选题
    topic = Topic(
        tenant_id=uuid4(),
        title="新能源产业链",
        description="光伏行业产能过剩问题",
        tags=["新能源"],
    )
    context = RunContext(tenant_id=uuid4(), topic_id=topic.id)

    # 测试严肃派
    print("\n" + "=" * 70)
    print("严肃派编辑产出")
    print("=" * 70)
    yan_su = registry.get_editor("yan-su-pai")
    if yan_su:
        draft1 = await yan_su.draft_article(topic, context)
        print(f"字数: {len(draft1.content)}")
        print(f"元数据: {draft1.metadata.get('style')}")
        print(f"\n内容预览:")
        print("-" * 70)
        print(draft1.content[:500] + "...")
    else:
        print("✗ 严肃派编辑未找到")

    # 测试犀利派
    print("\n" + "=" * 70)
    print("犀利派编辑产出")
    print("=" * 70)
    xi_li = registry.get_editor("xi-li-pai")
    if xi_li:
        draft2 = await xi_li.draft_article(topic, context)
        print(f"字数: {len(draft2.content)}")
        print(f"元数据: {draft2.metadata.get('style')}")
        print(f"\n内容预览:")
        print("-" * 70)
        print(draft2.content[:500] + "...")
    else:
        print("✗ 犀利派编辑未找到")

    # 风格对比
    if yan_su and xi_li:
        print("\n" + "=" * 70)
        print("风格对比")
        print("=" * 70)
        print(f"严肃派风格指纹: {yan_su.style_fingerprint().get('tone')}")
        print(f"犀利派风格指纹: {xi_li.style_fingerprint().get('tone')}")
        print(f"严肃派正式度: {yan_su.style_fingerprint().get('formality')}")
        print(f"犀利派正式度: {xi_li.style_fingerprint().get('formality')}")
        print(f"严肃派风险容忍: {yan_su.editor.preferences.get('risk_tolerance') if hasattr(yan_su, 'editor') else 'N/A'}")
        print(f"犀利派风险容忍: {xi_li.editor.preferences.get('risk_tolerance') if hasattr(xi_li, 'editor') else 'N/A'}")

    print("\n" + "=" * 70)
    print("✓ 多编辑风格测试完成")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
