#!/usr/bin/env python3
"""
content-factory A/B 测试示例

严肃派 vs 犀利派 并行产出同一选题,演示 SDK 的 `parallel_draft` 用法。

用法:
    uv run python examples/ab_test_run.py
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


async def main() -> None:
    from content_factory_sdk import InMemoryEventBus, discover_components
    from content_factory_sdk.ab_testing import StyleFingerprint, parallel_draft
    from content_factory_core.models import RunContext, Topic
    from content_factory_core.tenant_manager import get_tenant_manager
    from content_factory_topic import TopicProvider
    from content_factory_writing import WritingProvider

    print("🧪 content-factory A/B 测试示例")
    print("=" * 50)

    # 1. 创建租户
    tenant_mgr = get_tenant_manager()
    tenant = tenant_mgr.create_tenant(name="AB Team", slug="ab-test")
    print(f"\n[1/4] tenant:{tenant.id}")

    # 2. 选题
    topic = Topic(
        tenant_id=tenant.id,
        title="AI Agent 行业深度报告",
        tags=["AI", "Agent"],
    )
    context = RunContext(tenant_id=tenant.id, topic_id=topic.id)

    event_bus = InMemoryEventBus()
    topic_provider = TopicProvider(event_bus=event_bus)
    await topic_provider.approve_topic(topic, context)
    print(f"[2/4] topic approved:{topic.title}")

    # 3. A/B 测试:并行产出 严肃派 + 犀利派
    print("\n[3/4] 并行产出两个编辑的草稿...")
    drafts = await parallel_draft(
        topic=topic,
        editor_slugs=["yan-su-pai", "xi-li-pai"],
        context=context,
        registry=discover_components(),
        event_bus=event_bus,
    )
    for d in drafts:
        clen = d.get("length", len(d.get("content", "")) if isinstance(d.get("content"), str) else 0)
        print(f"  ✅ {d.get('editor', '?'):14s} | {clen:>5} chars | status={d.get('status')}")

    # 4. 风格指纹(展示 A/B 度量入口)
    print("\n[4/4] 当前已注册编辑风格:")
    editors_meta = discover_components().list_components()
    for slug in editors_meta.get("editors", []):
        ed = editors_meta["editors"][slug] if isinstance(editors_meta["editors"], dict) else None
        print(f"  - {slug}:{'meta=' + str(ed)[:60] if ed else '(no meta)'}")

    print("\n" + "=" * 50)
    print("✨ A/B 测试演示完成。真实场景下接 FeedbackTracker 记录阅读/点赞等回流数据。")


if __name__ == "__main__":
    asyncio.run(main())
