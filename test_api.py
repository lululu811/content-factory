#!/usr/bin/env python3
"""
测试 FastAPI 服务

使用 TestClient 直接测试，避免代理问题。
"""

from fastapi.testclient import TestClient
from content_factory_server.app import app


def test_api():
    """测试 API"""
    print("=" * 70)
    print("测试 FastAPI 服务")
    print("=" * 70)

    client = TestClient(app)

    # 1. 健康检查
    print("\n[1/4] 健康检查...")
    response = client.get("/health")
    assert response.status_code == 200
    health = response.json()
    print(f"  状态: {health['status']}")
    print(f"  版本: {health['version']}")
    print(f"  组件: {health['components']}")

    # 2. 创建运行
    print("\n[2/4] 创建运行...")
    response = client.post(
        "/runs",
        json={
            "tenant_name": "测试租户",
            "topic_title": "稀土行业深度分析",
        },
    )
    assert response.status_code == 200
    run = response.json()
    print(f"  Run ID: {run['run_id']}")
    print(f"  状态: {run['status']}")
    print(f"  选题: {run['topic_title']}")
    print(f"  编辑: {run['editor_slug']}")
    print(f"  草稿字数: {run['draft_length']}")
    print(f"  合规通过: {run['compliance_passed']}")
    print(f"  发布 URL: {run['publish_url']}")

    # 3. 获取运行
    print("\n[3/4] 获取运行详情...")
    run_id = run['run_id']
    response = client.get(f"/runs/{run_id}")
    assert response.status_code == 200
    run_detail = response.json()
    assert run_detail['run_id'] == run_id
    print(f"  ✓ 获取成功")

    # 4. 列出所有运行
    print("\n[4/4] 列出所有运行...")
    response = client.get("/runs")
    assert response.status_code == 200
    runs_list = response.json()
    print(f"  总数: {runs_list['total']}")
    print(f"  ✓ 列表获取成功")

    print("\n" + "=" * 70)
    print("✓ FastAPI 服务测试通过！")
    print("=" * 70)


if __name__ == "__main__":
    test_api()
