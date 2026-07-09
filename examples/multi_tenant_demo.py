#!/usr/bin/env python3
"""
content-factory 多租户隔离演示

创建 2 个租户,各自跑一次,然后展示他们的运行记录**完全隔离**。

用法:
    uv run python examples/multi_tenant_demo.py
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


async def main() -> None:
    from content_factory_core.tenant_manager import get_tenant_manager

    print("🏢 content-factory 多租户隔离演示")
    print("=" * 50)

    mgr = get_tenant_manager()

    # 1. 创建两个租户
    a = mgr.create_tenant(name="Alpha 投研团队", slug="alpha")
    b = mgr.create_tenant(name="Beta 投研团队", slug="beta")
    print(f"\n[1/3] 创建 2 个租户")
    print(f"  Alpha:id={a.id} slug={a.slug}")
    print(f"  Beta: id={b.id} slug={b.slug}")

    # 2. 给每个租户写入运行记录
    mgr.add_run(a.id, {"topic_title": "AI Agent 行业", "status": "completed"})
    mgr.add_run(a.id, {"topic_title": "液冷新卡点", "status": "failed"})
    mgr.add_run(b.id, {"topic_title": "玻璃基板 6 大环节", "status": "completed"})
    print("\n[2/3] 各写入运行记录")
    print(f"  Alpha:2 条")
    print(f"  Beta: 1 条")

    # 3. 查询隔离效果
    print("\n[3/3] 列表查询,验证隔离:")
    print(f"  Alpha 仅看到自己的记录:")
    for r in mgr.get_runs(a.id):
        print(f"    - {r.get('topic_title', '?'):30s} [{r.get('status', '?')}]")
    print(f"  Beta 仅看到自己的记录:")
    for r in mgr.get_runs(b.id):
        print(f"    - {r.get('topic_title', '?'):30s} [{r.get('status', '?')}]")

    print("\n" + "=" * 50)
    print("✨ 内存后端演示完成。生产配 CF_DATABASE_URL 后自动切 PostgreSQL schema-level 隔离。")


if __name__ == "__main__":
    asyncio.run(main())
