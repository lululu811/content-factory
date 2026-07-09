#!/usr/bin/env python3
"""
content-factory 数据源 fallback 演示

无 token 时所有数据源降级到 mock,但**不会报错**。
有 token 时自动切到真实 API,代码路径完全相同。

用法:
    uv run python examples/data_source_fallback.py
    # 想看真实数据:
    CF_TUSHARE_TOKEN=xxx uv run python examples/data_source_fallback.py
"""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


async def main() -> None:
    from content_factory_tushare import TushareDataSource

    print("🔌 content-factory 数据源 fallback 演示")
    print("=" * 50)

    src = TushareDataSource()
    has_token = bool(os.environ.get("CF_TUSHARE_TOKEN") or os.environ.get("CF_TUSHARE_BASE_URL"))

    print(f"\n[1/2] 数据源实例化")
    print(f"  CF_TUSHARE_TOKEN:{'已设置' if has_token else '未设置(mock 模式)'}")
    print(f"  backend:{'Tushare pro_api()' if has_token else 'mock data'}")

    print("\n[2/2] 拉取演示:")
    print("  $ await src.fetch_news(query='AI Agent', limit=3)")
    try:
        result = await src.fetch_news(query="AI Agent", limit=3)
        print(f"  ✅ 返回 {len(result)} 条")
        for it in result[:3]:
            print(f"    - {it.get('title', '')[:70]}")
    except Exception as e:  # noqa
        print(f"  ❌ 异常:{type(e).__name__}:{e}")
        print(f"  (生产环境下请检查网络连通性 / API 配额 / token 有效性)")

    print("\n" + "=" * 50)
    print("✨ 在任何环境下,代码路径完全相同——只是数据真假不同。")


if __name__ == "__main__":
    asyncio.run(main())
