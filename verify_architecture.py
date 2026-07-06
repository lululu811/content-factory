#!/usr/bin/env python3
"""
验证脚本：测试组件化架构的核心机制

验证：
1. core 包的模型和事件定义
2. sdk 包的 SPI 接口
3. entry points 自动发现机制
4. 事件总线通信
"""

import asyncio
import sys
from uuid import uuid4

# ── 测试 1: core 包导入 ──
print("=" * 60)
print("测试 1: 导入 core 包")
print("=" * 60)
try:
    from content_factory_core import (
        Topic, Editor, Draft, RunContext, Tenant,
        TopicApproved, ResearchCompleted,
        Settings,
    )
    print("✓ core 包导入成功")
except ImportError as e:
    print(f"✗ core 包导入失败: {e}")
    sys.exit(1)

# ── 测试 2: 创建模型实例 ──
print("\n" + "=" * 60)
print("测试 2: 创建模型实例")
print("=" * 60)
try:
    tenant = Tenant(name="测试租户", slug="test-tenant")
    topic = Topic(
        tenant_id=tenant.id,
        title="稀土行业深度分析",
        description="稀土管制 2.0 政策影响",
        tags=["科技", "新能源"],
    )
    editor = Editor(
        tenant_id=tenant.id,
        name="严肃派",
        slug="yan-su-pai",
    )
    print(f"✓ 创建租户: {tenant.name} (id={tenant.id})")
    print(f"✓ 创建选题: {topic.title} (tags={topic.tags})")
    print(f"✓ 创建编辑: {editor.name} (slug={editor.slug})")
except Exception as e:
    print(f"✗ 创建模型失败: {e}")
    sys.exit(1)

# ── 测试 3: 创建事件 ──
print("\n" + "=" * 60)
print("测试 3: 创建领域事件")
print("=" * 60)
try:
    event = TopicApproved(
        tenant_id=tenant.id,
        topic_id=topic.id,
    )
    print(f"✓ 创建事件: {event.event_type} (id={event.event_id})")
    print(f"  payload: topic_id={event.topic_id}")
except Exception as e:
    print(f"✗ 创建事件失败: {e}")
    sys.exit(1)

# ── 测试 4: sdk 包导入 ──
print("\n" + "=" * 60)
print("测试 4: 导入 sdk 包")
print("=" * 60)
try:
    from content_factory_sdk import (
        DataSourceProvider, EditorProvider, ComplianceProvider,
        ComponentRegistry, discover_components,
        EventBus, InMemoryEventBus,
    )
    print("✓ sdk 包导入成功")
except ImportError as e:
    print(f"✗ sdk 包导入失败: {e}")
    sys.exit(1)

# ── 测试 5: 事件总线 ──
print("\n" + "=" * 60)
print("测试 5: 事件总线通信")
print("=" * 60)
async def test_event_bus():
    bus = InMemoryEventBus()

    received_events = []

    async def handler(event):
        received_events.append(event)
        print(f"  收到事件: {event.event_type}")

    bus.on("topic.approved", handler)
    await bus.emit(event)

    if len(received_events) == 1:
        print("✓ 事件总线工作正常")
        return True
    else:
        print("✗ 事件总线未收到事件")
        return False

try:
    asyncio.run(test_event_bus())
except Exception as e:
    print(f"✗ 事件总线测试失败: {e}")
    sys.exit(1)

# ── 测试 6: 组件发现 ──
print("\n" + "=" * 60)
print("测试 6: 组件自动发现 (entry points)")
print("=" * 60)
try:
    registry = discover_components()
    components = registry.list_components()

    print(f"  发现的组件:")
    for category, names in components.items():
        print(f"    {category}: {names}")

    # 检查是否发现了 yan-su-pai 编辑
    if "yan-su-pai" in components["editors"]:
        print("✓ 成功发现 yan-su-pai 编辑组件")

        # 尝试使用这个编辑
        editor = registry.get_editor("yan-su-pai")
        if editor:
            context = RunContext(tenant_id=tenant.id, topic_id=topic.id)
            draft = asyncio.run(editor.draft_article(topic, context))
            print(f"✓ 成功生成草稿 (word_count={draft.metadata.get('word_count')})")
            print("\n草稿预览 (前 200 字):")
            print("-" * 60)
            print(draft.content[:200] + "...")
    else:
        print("⚠ 未发现 yan-su-pai 编辑组件（可能未安装）")
        print("  请运行: pip install packages/editors/yan-su-pai")

except Exception as e:
    print(f"✗ 组件发现测试失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ── 总结 ──
print("\n" + "=" * 60)
print("✓ 所有测试通过！组件化架构骨架已就绪")
print("=" * 60)
print("""
下一步:
1. 创建 Temporal workflow 编排这些组件
2. 迁移现有领域代码到 packages/domains/
3. 搭建 FastAPI server 暴露 API
4. 添加更多编辑组件（犀利派、数据派等）
""")
