"""
可观测性基础设施 (OpenTelemetry)

优雅降级: 未安装 opentelemetry 时使用本地日志实现。
"""
from contextlib import contextmanager
from typing import Any, Generator, Optional
import time

import structlog

logger = structlog.get_logger()

# 尝试导入 OpenTelemetry
try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import (
        BatchSpanProcessor,
        ConsoleSpanExporter,
    )
    from opentelemetry.sdk.resources import Resource
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    trace = None


class Metrics:
    """
    简单指标收集器（生产环境接入 Prometheus）
    """

    def __init__(self):
        self._counters: dict[str, int] = {}
        self._gauges: dict[str, float] = {}
        self._histograms: dict[str, list[float]] = {}

    def increment(self, name: str, value: int = 1, labels: Optional[dict] = None) -> None:
        """计数器递增"""
        key = self._make_key(name, labels)
        self._counters[key] = self._counters.get(key, 0) + value
        logger.debug("metric.counter", name=name, value=value, labels=labels)

    def gauge(self, name: str, value: float, labels: Optional[dict] = None) -> None:
        """设置仪表值"""
        key = self._make_key(name, labels)
        self._gauges[key] = value
        logger.debug("metric.gauge", name=name, value=value, labels=labels)

    def observe(self, name: str, value: float, labels: Optional[dict] = None) -> None:
        """记录直方图观测"""
        key = self._make_key(name, labels)
        self._histograms.setdefault(key, []).append(value)
        logger.debug("metric.histogram", name=name, value=value, labels=labels)

    def _make_key(self, name: str, labels: Optional[dict]) -> str:
        if not labels:
            return name
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"

    def snapshot(self) -> dict:
        """返回所有指标快照"""
        return {
            "counters": self._counters,
            "gauges": self._gauges,
            "histograms": {
                k: {
                    "count": len(v),
                    "sum": sum(v),
                    "avg": sum(v) / len(v) if v else 0,
                }
                for k, v in self._histograms.items()
            },
        }


# 全局指标
metrics = Metrics()


_initialized = False


def init_tracing(service_name: str = "content-factory") -> bool:
    """
    初始化 OpenTelemetry 追踪

    默认仅启用 TracerProvider，不附加导出器（避免污染 stdout）。
    需要导出 span 时，设置环境变量:
      CF_TRACE_CONSOLE=1   控制台输出
      CF_TRACE_OTLP=1      OTLP 协议（需安装 opentelemetry-exporter-otlp）

    Returns:
        是否成功初始化（False 表示使用降级模式）
    """
    global _initialized
    if _initialized:
        return True

    if not OTEL_AVAILABLE:
        logger.info("telemetry.fallback", reason="opentelemetry not installed")
        return False

    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)

    import os
    if os.getenv("CF_TRACE_CONSOLE"):
        try:
            processor = BatchSpanProcessor(ConsoleSpanExporter())
            provider.add_span_processor(processor)
        except Exception:
            pass  # pytest 等环境下 stdout 可能被捕获

    trace.set_tracer_provider(provider)
    _initialized = True
    logger.info("telemetry.initialized", service=service_name)
    return True


@contextmanager
def trace_span(name: str, attributes: Optional[dict[str, Any]] = None) -> Generator:
    """
    追踪一个代码段

    Usage:
        with trace_span("article_production", {"tenant": "abc"}):
            # 你的代码
            pass
    """
    start_time = time.time()

    if OTEL_AVAILABLE:
        tracer = trace.get_tracer("content-factory")
        with tracer.start_as_current_span(name) as span:
            if attributes:
                for k, v in attributes.items():
                    span.set_attribute(k, str(v))
            try:
                yield span
            except Exception as e:
                span.set_attribute("error", str(e))
                span.set_status(trace.Status(trace.StatusCode.ERROR))
                raise
    else:
        # 降级模式：只记录日志
        logger.debug("trace.start", name=name, attributes=attributes)
        try:
            yield
        finally:
            duration = (time.time() - start_time) * 1000
            logger.debug("trace.end", name=name, duration_ms=f"{duration:.2f}")
            metrics.observe("span.duration", duration, {"span": name})


def record_workflow_run(
    tenant_id: str,
    editor_slug: str,
    duration_seconds: float,
    compliance_passed: bool,
    status: str,
) -> None:
    """记录工作流运行指标"""
    metrics.increment("workflow.runs.total", labels={
        "tenant": tenant_id,
        "editor": editor_slug,
        "status": status,
    })
    metrics.observe("workflow.runs.duration", duration_seconds, labels={
        "tenant": tenant_id,
        "editor": editor_slug,
    })
    metrics.increment("workflow.compliance.passed" if compliance_passed else "workflow.compliance.failed")


def get_metrics_snapshot() -> dict:
    """获取当前指标快照"""
    return metrics.snapshot()
