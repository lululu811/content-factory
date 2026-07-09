"""
Temporal Workflow 定义

文章生产工作流（ArticleProductionWorkflow）：
  - 支持断点续跑（Signal/Query）
  - 自动重试（RetryPolicy）
  - 人工审批（Query + Signal）
  - 长时间运行（Timeouts）
"""

import asyncio
from dataclasses import dataclass
from datetime import timedelta
from uuid import uuid4

try:
    from temporalio import activity, workflow
    from temporalio.common import RetryPolicy

    TEMPORAL_AVAILABLE = True
except ImportError:
    TEMPORAL_AVAILABLE = False

    class _FakeDefn:
        """Fallback decorator with .defn attribute"""

        def __call__(self, fn):
            return fn

        @property
        def defn(self):
            return self

    activity = _FakeDefn()
    workflow = _FakeDefn()

    class RetryPolicy:
        def __init__(self, **kwargs):
            pass


@dataclass
class ArticleProductionInput:
    """工作流输入"""

    tenant_id: str
    topic_title: str
    editor_slug: str | None = None
    require_manual_approval: bool = False


@dataclass
class ArticleProductionOutput:
    """工作流输出"""

    run_id: str
    article_url: str | None = None
    status: str = "pending"
    error: str | None = None


# ============== Activities ==============


@activity.defn
async def discover_and_approve_topic(input: ArticleProductionInput) -> str:
    """
    Activity 1: 选题发现与批准
    超时: 5 分钟, 重试: 3 次
    """
    # 实际实现调用 TopicProvider
    print(f"[Activity] 选题: {input.topic_title}")
    await asyncio.sleep(0.5)
    return f"topic-{uuid4().hex[:8]}"


@activity.defn
async def run_research(topic_id: str) -> str:
    """
    Activity 2: 深度研究
    超时: 30 分钟（可能调用外部 API）, 重试: 2 次
    """
    print(f"[Activity] 研究: {topic_id}")
    await asyncio.sleep(1)
    return f"research-{uuid4().hex[:8]}"


@activity.defn
async def write_draft(topic_id: str, editor_slug: str) -> str:
    """
    Activity 3: 写作
    超时: 15 分钟
    """
    print(f"[Activity] 写作: editor={editor_slug}")
    await asyncio.sleep(1)
    return f"draft-{uuid4().hex[:8]}"


@activity.defn
async def run_compliance(draft_id: str) -> dict:
    """
    Activity 4: 合规检查
    不重试（失败需要人工介入）
    """
    print(f"[Activity] 合规检查: {draft_id}")
    await asyncio.sleep(0.5)
    return {"passed": True, "risk_level": "low", "issues": []}


@activity.defn
async def publish_article(draft_id: str) -> str:
    """
    Activity 5: 发布
    超时: 10 分钟, 重试: 5 次
    """
    print(f"[Activity] 发布: {draft_id}")
    await asyncio.sleep(0.5)
    return f"https://mp.weixin.qq.com/s/{uuid4().hex[:12]}"


@activity.defn
async def request_manual_approval(run_id: str, context: dict) -> bool:
    """
    Activity 6: 等待人工审批
    使用 workflow.wait_condition 实现长时间等待
    """
    # 实际实现：通过 Signal 接收审批结果
    print(f"[Activity] 等待人工审批: {run_id}")
    return True


# ============== Workflow ==============


if TEMPORAL_AVAILABLE:

    @workflow.defn
    class ArticleProductionWorkflow:
        """
        文章生产工作流

        特性:
        - 每个 Activity 独立重试策略
        - 支持人工审批（Signal/Query）
        - 30 天超时（长尾文章可能需要多天完成）
        - 可查询进度（Query）
        """

        def __init__(self) -> None:
            self._status = "initialized"
            self._progress = 0
            self._approval_granted = False
            self._current_activity = ""

        @workflow.run
        async def run(self, input: ArticleProductionInput) -> ArticleProductionOutput:
            run_id = workflow.info().workflow_id
            self._status = "running"

            retry_policy = RetryPolicy(
                maximum_attempts=3,
                initial_interval=timedelta(seconds=5),
                backoff_coefficient=2.0,
            )

            try:
                # 1. 选题
                self._current_activity = "topic_discovery"
                topic_id = await workflow.execute_activity(
                    discover_and_approve_topic,
                    input,
                    start_to_close_timeout=timedelta(minutes=5),
                    retry_policy=retry_policy,
                )
                self._progress = 20

                # 2. 研究
                self._current_activity = "research"
                await workflow.execute_activity(
                    run_research,
                    topic_id,
                    start_to_close_timeout=timedelta(minutes=30),
                    retry_policy=RetryPolicy(maximum_attempts=2),
                )
                self._progress = 40

                # 3. 写作
                self._current_activity = "writing"
                editor_slug = input.editor_slug or "yan-su-pai"
                draft_id = await workflow.execute_activity(
                    write_draft,
                    [topic_id, editor_slug],
                    start_to_close_timeout=timedelta(minutes=15),
                )
                self._progress = 60

                # 4. 合规检查（不重试）
                self._current_activity = "compliance"
                compliance_result = await workflow.execute_activity(
                    run_compliance,
                    draft_id,
                    start_to_close_timeout=timedelta(minutes=5),
                    retry_policy=RetryPolicy(maximum_attempts=1),
                )
                self._progress = 80

                if not compliance_result.get("passed"):
                    self._status = "failed"
                    return ArticleProductionOutput(
                        run_id=run_id,
                        status="compliance_failed",
                        error="合规检查未通过",
                    )

                # 5. 可选：人工审批
                if input.require_manual_approval:
                    self._current_activity = "awaiting_approval"
                    await workflow.wait_condition(
                        lambda: self._approval_granted,
                        timeout=timedelta(days=7),
                    )
                    if not self._approval_granted:
                        return ArticleProductionOutput(
                            run_id=run_id,
                            status="approval_timeout",
                            error="人工审批超时",
                        )

                # 6. 发布
                self._current_activity = "publishing"
                article_url = await workflow.execute_activity(
                    publish_article,
                    draft_id,
                    start_to_close_timeout=timedelta(minutes=10),
                    retry_policy=RetryPolicy(
                        maximum_attempts=5,
                        initial_interval=timedelta(seconds=10),
                    ),
                )
                self._progress = 100
                self._status = "completed"

                return ArticleProductionOutput(
                    run_id=run_id,
                    article_url=article_url,
                    status="completed",
                )

            except Exception as e:
                self._status = "failed"
                return ArticleProductionOutput(
                    run_id=run_id,
                    status="failed",
                    error=str(e),
                )

        # ============== Signals ==============

        @workflow.signal
        async def grant_approval(self) -> None:
            """Signal: 批准"""
            self._approval_granted = True

        @workflow.signal
        async def reject_approval(self) -> None:
            """Signal: 拒绝"""
            self._approval_granted = False

        # ============== Queries ==============

        @workflow.query
        def get_progress(self) -> int:
            """Query: 获取进度百分比"""
            return self._progress

        @workflow.query
        def get_status(self) -> str:
            """Query: 获取当前状态"""
            return self._status

        @workflow.query
        def get_current_activity(self) -> str:
            """Query: 获取当前 Activity"""
            return self._current_activity

else:
    # Temporal 未安装时的占位
    class ArticleProductionWorkflow:
        """占位：需要安装 temporalio"""

        def __init__(self, *args, **kwargs):
            raise RuntimeError("temporalio 未安装。运行: pip install temporalio")
