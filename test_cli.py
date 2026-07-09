#!/usr/bin/env python3
"""
测试 CLI 命令

使用 FastAPI TestClient 测试 CLI 逻辑。
"""

from content_factory_server.app import app
from fastapi.testclient import TestClient


def test_cli_commands():
    """测试 CLI 对应的 API 端点"""
    client = TestClient(app)

    print("=" * 70)
    print("测试 CLI 命令")
    print("=" * 70)

    # 1. health
    print("\n[1/4] cf health")
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    print(f"  状态: {data['status']}")
    print(f"  版本: {data['version']}")
    print("  ✓ 健康检查通过")

    # 2. create
    print("\n[2/4] cf create 测试租户 --topic 稀土分析")
    response = client.post(
        "/runs",
        json={
            "tenant_name": "测试租户",
            "topic_title": "稀土分析",
        },
    )
    assert response.status_code == 200
    run = response.json()
    print(f"  Run ID: {run['run_id']}")
    print(f"  选题: {run['topic_title']}")
    print(f"  编辑: {run['editor_slug']}")
    print("  ✓ 创建运行成功")

    # 3. list
    print("\n[3/4] cf list")
    response = client.get("/runs")
    assert response.status_code == 200
    runs = response.json()
    print(f"  总数: {runs['total']}")
    print("  ✓ 列出运行成功")

    # 4. status
    print("\n[4/4] cf status <run_id>")
    run_id = run["run_id"]
    response = client.get(f"/runs/{run_id}")
    assert response.status_code == 200
    run_detail = response.json()
    print(f"  Run ID: {run_detail['run_id']}")
    print(f"  状态: {run_detail['status']}")
    print("  ✓ 获取运行详情成功")

    # 5. components
    print("\n[5/4] cf components")
    response = client.get("/health")
    data = response.json()
    print("  组件类别:")
    for category, names in data["components"].items():
        print(f"    {category}: {', '.join(names) if names else '无'}")
    print("  ✓ 列出组件成功")

    print("\n" + "=" * 70)
    print("✓ CLI 命令测试通过！")
    print("=" * 70)
    print("""
使用说明:
  1. 启动 API 服务: uv run uvicorn content_factory_server.app:app --reload
  2. 使用 CLI:
     - cf health              # 检查服务状态
     - cf create 租户名        # 创建运行
     - cf list                # 列出运行
     - cf status <run_id>     # 查看运行详情
     - cf components          # 列出组件
""")


if __name__ == "__main__":
    test_cli_commands()
