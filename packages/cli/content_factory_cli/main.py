"""
CLI 主程序

提供命令行接口，调用 API 服务。
"""

import httpx
import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(help="Content Factory CLI - 投研内容 AI 编辑部")
console = Console()

# 默认 API 地址
DEFAULT_API_URL = "http://127.0.0.1:8000"


def get_client(base_url: str = DEFAULT_API_URL) -> httpx.Client:
    """获取 HTTP 客户端"""
    return httpx.Client(base_url=base_url, timeout=30.0, trust_env=False)


@app.command()
def health(
    api_url: str = typer.Option(DEFAULT_API_URL, "--api-url", "-u", help="API 服务地址"),
):
    """检查 API 服务健康状态"""
    try:
        with get_client(api_url) as client:
            response = client.get("/health")
            response.raise_for_status()
            data = response.json()

            console.print(f"[green]✓[/green] 服务状态: {data['status']}")
            console.print(f"版本: {data['version']}")
            console.print("\n组件:")
            for category, names in data["components"].items():
                console.print(f"  {category}: {', '.join(names) if names else '无'}")
    except Exception as e:
        console.print(f"[red]✗[/red] 服务不可用: {e}")
        raise typer.Exit(1) from e


@app.command()
def create(
    tenant_name: str = typer.Argument(..., help="租户名称"),
    topic_title: str | None = typer.Option(None, "--topic", "-t", help="选题标题"),
    editor_slug: str | None = typer.Option(None, "--editor", "-e", help="编辑 slug"),
    api_url: str = typer.Option(DEFAULT_API_URL, "--api-url", "-u", help="API 服务地址"),
):
    """创建新的文章生产运行"""
    console.print(f"[blue]创建运行[/blue]: 租户={tenant_name}, 选题={topic_title or '自动'}")

    try:
        with get_client(api_url) as client:
            payload = {"tenant_name": tenant_name}
            if topic_title:
                payload["topic_title"] = topic_title
            if editor_slug:
                payload["editor_slug"] = editor_slug

            response = client.post("/runs", json=payload)
            response.raise_for_status()
            data = response.json()

            console.print("\n[green]✓ 运行创建成功[/green]")
            console.print(f"Run ID: {data['run_id']}")
            console.print(f"状态: {data['status']}")
            console.print(f"选题: {data['topic_title']}")
            console.print(f"编辑: {data['editor_slug']}")
            console.print(f"草稿字数: {data['draft_length']}")
            console.print(f"合规通过: {'是' if data['compliance_passed'] else '否'}")
            if data.get("publish_url"):
                console.print(f"发布 URL: {data['publish_url']}")
    except Exception as e:
        console.print(f"[red]✗ 创建失败: {e}")
        raise typer.Exit(1) from e


@app.command(name="list")
def list_runs(
    api_url: str = typer.Option(DEFAULT_API_URL, "--api-url", "-u", help="API 服务地址"),
):
    """列出所有运行"""
    try:
        with get_client(api_url) as client:
            response = client.get("/runs")
            response.raise_for_status()
            data = response.json()

            if data["total"] == 0:
                console.print("暂无运行记录")
                return

            table = Table(title=f"运行列表（共 {data['total']} 条）")
            table.add_column("Run ID", style="cyan")
            table.add_column("状态", style="green")
            table.add_column("选题")
            table.add_column("编辑")
            table.add_column("字数")
            table.add_column("合规")

            for run in data["runs"]:
                table.add_row(
                    run["run_id"][:8] + "...",
                    run["status"],
                    run["topic_title"][:20],
                    run["editor_slug"],
                    str(run["draft_length"]),
                    "✓" if run["compliance_passed"] else "✗",
                )

            console.print(table)
    except Exception as e:
        console.print(f"[red]✗ 获取失败: {e}")
        raise typer.Exit(1) from e


@app.command()
def status(
    run_id: str = typer.Argument(..., help="Run ID"),
    api_url: str = typer.Option(DEFAULT_API_URL, "--api-url", "-u", help="API 服务地址"),
):
    """获取运行详情"""
    try:
        with get_client(api_url) as client:
            response = client.get(f"/runs/{run_id}")
            response.raise_for_status()
            data = response.json()

            console.print(f"\n[cyan]Run ID:[/cyan] {data['run_id']}")
            console.print(f"[cyan]状态:[/cyan] {data['status']}")
            console.print(f"[cyan]选题:[/cyan] {data['topic_title']}")
            console.print(f"[cyan]编辑:[/cyan] {data['editor_slug']}")
            console.print(f"[cyan]草稿字数:[/cyan] {data['draft_length']}")
            console.print(f"[cyan]合规通过:[/cyan] {'是' if data['compliance_passed'] else '否'}")
            if data.get("publish_url"):
                console.print(f"[cyan]发布 URL:[/cyan] {data['publish_url']}")
    except Exception as e:
        console.print(f"[red]✗ 获取失败: {e}")
        raise typer.Exit(1) from e


@app.command()
def components(
    api_url: str = typer.Option(DEFAULT_API_URL, "--api-url", "-u", help="API 服务地址"),
):
    """列出所有已安装的组件"""
    try:
        with get_client(api_url) as client:
            response = client.get("/health")
            response.raise_for_status()
            data = response.json()

            table = Table(title="已安装组件")
            table.add_column("类别", style="cyan")
            table.add_column("组件", style="green")

            for category, names in data["components"].items():
                table.add_row(category, ", ".join(names) if names else "无")

            console.print(table)
    except Exception as e:
        console.print(f"[red]✗ 获取失败: {e}")
        raise typer.Exit(1) from e


if __name__ == "__main__":
    app()
