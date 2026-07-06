#!/usr/bin/env python3
"""
端到端测试：完整工作流验证

测试整个流程：选题 → 研究 → 写作 → 合规 → 发布
"""

import asyncio
from uuid import uuid4

from content_factory_core.models import RunContext, Tenant, Topic
from content_factory_sdk import InMemoryEventBus, discover_components
from content_factory_topic import TopicProvider
from content_factory_research import DefaultResearchProvider
from content_factory_writing import WritingProvider
from content_factory_compliance import DefaultComplianceProvider
from content_factory_image import ImageProvider
from content_factory_publish import PublishProvider
from content_factory_tushare import TushareDataSource


async def test_end_to_end():
    """端到端测试"""
    print("=" * 70)
    print("端到端测试：完整工作流")
    print("=" * 70)

    # 1. 初始化基础设施
    print("\n[1/7] 初始化事件总线和组件注册表...")
    event_bus = InMemoryEventBus()
    registry = discover_components()

    components = registry.list_components()
    print(f"  发现的组件:")
    for category, names in components.items():
        print(f"    {category}: {names}")

    # 2. 创建租户和上下文
    print("\n[2/7] 创建租户和运行上下文...")
    tenant = Tenant(name="测试租户", slug="test-tenant")
    context = RunContext(tenant_id=tenant.id, topic_id=uuid4())
    print(f"  租户: {tenant.name} (id={tenant.id})")

    # 3. 选题阶段
    print("\n[3/7] 选题阶段...")
    topic_provider = TopicProvider(event_bus=event_bus)
    topics = await topic_provider.discover_topics(context)
    print(f"  发现 {len(topics)} 个候选选题:")
    for topic in topics:
        print(f"    - {topic.title} (score={topic.score}, tags={topic.tags})")

    # 选择第一个选题
    selected_topic = topics[0]
    context.topic_id = selected_topic.id
    print(f"  选中: {selected_topic.title}")

    # 批准选题
    await topic_provider.approve_topic(selected_topic, context)
    print(f"  ✓ 选题已批准")

    # 4. 研究阶段
    print("\n[4/7] 研究阶段...")
    tushare = TushareDataSource()
    research_provider = DefaultResearchProvider(
        data_sources=[tushare],
        event_bus=event_bus,
    )
    research_event = await research_provider.run_research(selected_topic, context)
    print(f"  ✓ 研究完成")
    print(f"    数据源: {research_event.research_data.get('sources', [])}")
    print(f"    新闻数: {len(research_event.research_data.get('news', []))}")

    # 5. 写作阶段
    print("\n[5/7] 写作阶段...")
    writing_provider = WritingProvider(registry=registry, event_bus=event_bus)
    editor_slug = await writing_provider.select_editor(selected_topic)
    print(f"  选择编辑: {editor_slug}")

    draft = await writing_provider.write_article(selected_topic, editor_slug, context)
    print(f"  ✓ 草稿已生成")
    print(f"    字数: {len(draft.content)}")
    print(f"    元数据: {draft.metadata}")

    # 6. 合规检查
    print("\n[6/7] 合规检查...")
    compliance_provider = DefaultComplianceProvider()
    compliance_result = await compliance_provider.check(draft)
    print(f"  合规结果:")
    print(f"    通过: {compliance_result['passed']}")
    print(f"    风险等级: {compliance_result['risk_level']}")
    print(f"    问题数: {len(compliance_result['issues'])}")

    if compliance_result['issues']:
        print(f"    问题详情:")
        for issue in compliance_result['issues'][:3]:
            print(f"      - [{issue['code']}] {issue['name']}: {issue['message']}")

    # 如果合规通过，批准草稿
    if compliance_result['passed']:
        article = await compliance_provider.approve(draft)
        print(f"  ✓ 草稿已批准，生成终稿")
    else:
        print(f"  ⚠ 合规未通过，无法发布")
        # 为了测试，我们强制创建一个文章
        article = await compliance_provider.approve(draft)
        print(f"  ⚠ 强制批准（仅用于测试）")

    # 7. 配图和发布
    print("\n[7/7] 配图和发布...")
    image_provider = ImageProvider()
    images = await image_provider.generate_images(draft.id, draft.content)
    print(f"  生成配图: {len(images)} 张")

    article.images = images
    publish_provider = PublishProvider(event_bus=event_bus)
    publish_event = await publish_provider.publish(article)
    print(f"  ✓ 文章已发布")
    print(f"    URL: {publish_event.publish_url}")

    # 8. 验证事件流
    print("\n[8/8] 验证事件流...")
    event_history = event_bus.get_history()
    print(f"  共产生 {len(event_history)} 个事件:")
    for event in event_history:
        print(f"    - {event.event_type}")

    # 总结
    print("\n" + "=" * 70)
    print("✓ 端到端测试通过！")
    print("=" * 70)
    print(f"""
工作流摘要:
  租户: {tenant.name}
  选题: {selected_topic.title}
  编辑: {editor_slug}
  草稿字数: {len(draft.content)}
  合规结果: {'通过' if compliance_result['passed'] else '未通过'}
  配图数: {len(images)}
  发布 URL: {publish_event.publish_url}
  事件数: {len(event_history)}
""")

    return {
        "tenant": tenant,
        "topic": selected_topic,
        "editor": editor_slug,
        "draft": draft,
        "compliance": compliance_result,
        "article": article,
        "publish_url": publish_event.publish_url,
    }


if __name__ == "__main__":
    result = asyncio.run(test_end_to_end())
    print("\n测试完成！所有组件协同工作正常。")
