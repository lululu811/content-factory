#!/usr/bin/env python3
"""
content-factory 30 秒端到端 quickstart

无需任何外部 API token,使用 mock 数据源跑完整流水线:
discover_topics → approve_topic → run_research → write_article → compliance check → publish。

用法:
    uv run python examples/quickstart_e2e.py

输出:
    - 控制台:每个阶段状态 + 最终 URL(MOCK 微信公众号返回)
    - htmlcov/ 中:覆盖率报告(若已安装 pytest-cov)
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# 让脚本能直接 `python examples/quickstart_e2e.py`,把仓库根加进 sys.path
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


async def main() -> None:
    # ───── 导入只用 SDK 公开 API,业务代码不直接 import 任何 adapter ─────
    from content_factory_sdk import (
        InMemoryEventBus,
        discover_components,
    )
    from content_factory_sdk.ab_testing import parallel_draft
    from content_factory_core.models import RunContext, Tenant, Topic
    from content_factory_core.tenant_manager import get_tenant_manager
    from content_factory_topic import TopicProvider
    from content_factory_research import DefaultResearchProvider
    from content_factory_writing import WritingProvider
    from content_factory_compliance import DefaultComplianceProvider
    from content_factory_publish import PublishProvider
    from content_factory_tushare import TushareDataSource

    print("🚀 content-factory quickstart")
    print("=" * 50)

    # 1. 组件发现(走 registry,不直接 import)
    registry = discover_components()
    print("\n[1/6] 已注册组件:", registry.list_components())

    # 2. 创建租户
    print("\n[2/6] 创建内存租户")
    tenant_mgr = get_tenant_manager()
    tenant = tenant_mgr.create_tenant(name="Quickstart Team", slug="quickstart")
    print(f"  ✅ tenant id={tenant.id}")

    # 3. 选题
    print("\n[3/6] 选题(默认 topic,实际生产可走 TrendRadar)")
    event_bus = InMemoryEventBus()
    topic_provider = TopicProvider(event_bus=event_bus)
    topic = Topic(tenant_id=tenant.id, title="AI Agent 行业深度报告", tags=["AI"])
    context = RunContext(tenant_id=tenant.id, topic_id=topic.id)
    await topic_provider.approve_topic(topic, context)
    print(f"  ✅ topic approved:{topic.title}")

    # 4. 研究(mock 数据)
    print("\n[4/6] 研究(走 TushareDataSource,无 token 时自动降级 mock)")
    research = DefaultResearchProvider(
        data_sources=[TushareDataSource()],
        event_bus=event_bus,
    )
    await research.run_research(topic, context)
    print("  ✅ research completed")

    # 5. 写作 + 合规
    print("\n[5/6] 写作 + 合规检查")
    writing = WritingProvider(registry=registry, event_bus=event_bus)
    draft = await writing.write_article(topic, editor_slug="yan-su-pai", context=context)
    print(f"  ✅ draft ready ({len(draft.content or '')} chars)")

    compliance = DefaultComplianceProvider()
    result = await compliance.check(draft)
    print(f"  {'✅' if result['passed'] else '⚠️'} compliance {result['risk_level']} "
          f"({len(result['issues'])} issues)")
    if not result["passed"]:
        print("  ⚠️  真实场景下,publish --strict 会阻断。请补充 frontmatter 或修复 issue。")
        print("     此 quickstart 跳过 publish 步骤,仅展示流水线。")
        return

    # 6. 发布(mock 微信)
    print("\n[6/6] 发布(mock 微信,无 CF_WECHAT_APPID 时降级)")
    publisher = PublishProvider()
    event = await publisher.publish(draft)
    print(f"  ✅ published:{event.publish_url}")

    print("\n" + "=" * 50)
    print("✨ Done. 如上即完成一次端到端 mock 推送。")
    print("   真实数据接入:配置 CF_TUSHARE_TOKEN / CF_WECHAT_APPID → 重跑。")


if __name__ == "__main__":
    asyncio.run(main())
