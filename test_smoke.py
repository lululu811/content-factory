#!/usr/bin/env python3
"""
冒烟测试套件

验证所有核心功能正常工作。
"""

import asyncio
import sys
from uuid import uuid4

from content_factory_core.models import RunContext, Tenant, Topic
from content_factory_sdk import InMemoryEventBus, discover_components


def test_component_discovery():
    """测试 1: 组件发现"""
    print("\n" + "=" * 70)
    print("冒烟测试 1: 组件发现")
    print("=" * 70)

    registry = discover_components()
    components = registry.list_components()

    print(f"发现的组件:")
    for category, names in components.items():
        print(f"  {category}: {names}")

    # 验证关键组件存在
    assert "tushare" in components["data_sources"], "tushare 数据源缺失"
    assert "yan-su-pai" in components["editors"], "yan-su-pai 编辑缺失"
    assert "default" in components["compliance"], "compliance 组件缺失"

    print("✓ 组件发现测试通过")
    return True


async def test_event_bus():
    """测试 2: 事件总线"""
    print("\n" + "=" * 70)
    print("冒烟测试 2: 事件总线")
    print("=" * 70)

    from content_factory_core.events import TopicApproved

    event_bus = InMemoryEventBus()
    received = []

    async def handler(event):
        received.append(event)

    event_bus.on("topic.approved", handler)

    tenant = Tenant(name="test", slug="test")
    event = TopicApproved(tenant_id=tenant.id, topic_id=uuid4())
    await event_bus.emit(event)

    assert len(received) == 1, "事件未收到"
    assert received[0].event_type == "topic.approved", "事件类型错误"

    print("✓ 事件总线测试通过")
    return True


async def test_compliance_check():
    """测试 3: 合规检查"""
    print("\n" + "=" * 70)
    print("冒烟测试 3: 合规检查")
    print("=" * 70)

    from content_factory_core.models import Draft
    from content_factory_compliance import DefaultComplianceProvider

    provider = DefaultComplianceProvider()
    draft = Draft(
        tenant_id=uuid4(),
        topic_id=uuid4(),
        editor_id=uuid4(),
        content="# 测试文章\n\n## 公司 5 分类\n" + "**公司A**\n" * 25,
        metadata={"slug": "test"},
    )

    result = await provider.check(draft)
    assert "passed" in result, "结果缺少 passed 字段"
    assert "risk_level" in result, "结果缺少 risk_level 字段"

    print(f"  合规结果: passed={result['passed']}, risk={result['risk_level']}")
    print("✓ 合规检查测试通过")
    return True


async def test_editor_draft():
    """测试 4: 编辑生成草稿"""
    print("\n" + "=" * 70)
    print("冒烟测试 4: 编辑生成草稿")
    print("=" * 70)

    registry = discover_components()
    editor = registry.get_editor("yan-su-pai")
    assert editor is not None, "编辑未找到"

    topic = Topic(
        tenant_id=uuid4(),
        title="测试选题",
        tags=["科技"],
    )
    context = RunContext(tenant_id=uuid4(), topic_id=topic.id)

    draft = await editor.draft_article(topic, context)
    assert len(draft.content) > 0, "草稿为空"
    assert draft.editor_id is not None, "编辑 ID 缺失"

    print(f"  草稿字数: {len(draft.content)}")
    print("✓ 编辑生成草稿测试通过")
    return True


async def test_data_source():
    """测试 5: 数据源"""
    print("\n" + "=" * 70)
    print("冒烟测试 5: 数据源")
    print("=" * 70)

    from content_factory_tushare import TushareDataSource

    source = TushareDataSource()
    news = await source.fetch_news("稀土", limit=5)
    assert len(news) > 0, "新闻为空"

    print(f"  获取新闻数: {len(news)}")
    print("✓ 数据源测试通过")
    return True


async def test_full_workflow():
    """测试 6: 完整工作流"""
    print("\n" + "=" * 70)
    print("冒烟测试 6: 完整工作流")
    print("=" * 70)

    from content_factory_topic import TopicProvider
    from content_factory_research import DefaultResearchProvider
    from content_factory_writing import WritingProvider
    from content_factory_compliance import DefaultComplianceProvider
    from content_factory_image import ImageProvider
    from content_factory_publish import PublishProvider
    from content_factory_tushare import TushareDataSource

    event_bus = InMemoryEventBus()
    registry = discover_components()

    tenant = Tenant(name="test", slug="test")
    context = RunContext(tenant_id=tenant.id, topic_id=uuid4())

    # 选题
    topic_provider = TopicProvider(event_bus=event_bus)
    topics = await topic_provider.discover_topics(context)
    topic = topics[0]
    context.topic_id = topic.id
    await topic_provider.approve_topic(topic, context)  # 触发 topic.approved 事件

    # 研究
    tushare = TushareDataSource()
    research_provider = DefaultResearchProvider(data_sources=[tushare], event_bus=event_bus)
    await research_provider.run_research(topic, context)

    # 写作
    writing_provider = WritingProvider(registry=registry, event_bus=event_bus)
    draft = await writing_provider.write_article(topic, "yan-su-pai", context)

    # 合规
    compliance_provider = DefaultComplianceProvider()
    result = await compliance_provider.check(draft)

    # 发布
    article = await compliance_provider.approve(draft)
    image_provider = ImageProvider()
    images = await image_provider.generate_images(draft.id, draft.content)
    article.images = images

    publish_provider = PublishProvider(event_bus=event_bus)
    publish_event = await publish_provider.publish(article)

    # 验证事件流
    events = event_bus.get_history()
    assert len(events) == 4, f"事件数错误: {len(events)}"

    print(f"  事件流: {[e.event_type for e in events]}")
    print(f"  发布 URL: {publish_event.publish_url}")
    print("✓ 完整工作流测试通过")
    return True


async def main():
    """运行所有冒烟测试"""
    print("=" * 70)
    print("冒烟测试套件")
    print("=" * 70)

    tests = [
        ("组件发现", lambda: test_component_discovery()),
        ("事件总线", test_event_bus),
        ("合规检查", test_compliance_check),
        ("编辑生成草稿", test_editor_draft),
        ("数据源", test_data_source),
        ("完整工作流", test_full_workflow),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            result = test_func()
            if asyncio.iscoroutine(result):
                result = await result
            if result:
                passed += 1
            else:
                failed += 1
                print(f"✗ {name} 测试失败")
        except Exception as e:
            failed += 1
            print(f"✗ {name} 测试异常: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 70)
    print(f"冒烟测试结果: {passed} 通过, {failed} 失败")
    print("=" * 70)

    if failed > 0:
        sys.exit(1)
    else:
        print("\n✓ 所有冒烟测试通过！")
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
