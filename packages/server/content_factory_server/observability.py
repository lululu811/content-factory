"""
可观测性基础设施 (OpenTelemetry + Prometheus)

优雅降级策略:
  - 未安装 opentelemetry: 本地 structlog + 内存 Metrics
  - 安装了 opentelemetry 但未装 otlp exporter: 仅启用 TracerProvider
  - 装了 otlp exporter + 设置 CF_TRACE_OTLP=1: 启用 OTLP span 导出
  - 装了 prometheus_client: /metrics 输出 Prometheus exposition 格式
    否则 /metrics 返回 JSON 快照(向后兼容)

环境变量:
  CF_TRACE_CONSOLE=1                  ConsoleSpanExporter (调试)
  CF_TRACE_OTLP=1                     OTLPSpanExporter (需装 exporter)
  CF_TRACE_OTLP_ENDPOINT=http://...   OTLP endpoint (默认 http://localhost:4318/v1/traces)
  CF_METRICS_BACKEND=prometheus       显式启用 prometheus_client 输出
"""

import os
import time
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

import structlog

logger = structlog.get_logger()

# ── OpenTelemetry ──
try:
    from opentelemetry import trace
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import (
        BatchSpanProcessor,
        ConsoleSpanExporter,
    )

    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    trace = None

# Optional: OTLP exporter
try:
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
        OTLPSpanExporter as HTTPOTLPSpanExporter,
    )

    OTLP_HTTP_AVAILABLE = True
except ImportError:
    OTLP_HTTP_AVAILABLE = False


# Optional: prometheus_client
try:
    from prometheus_client import (
        CONTENT_TYPE_LATEST,
        CollectorRegistry,
        Counter,
        Gauge,
        Histogram,
        generate_latest,
    )

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    CONTENT_TYPE_LATEST = "text/plain; version=0.0.4; charset=utf-8"


def _make_prometheus_label_key(name: str, labels: dict | None) -> tuple:
    """把 (name, labels) 序列化成稳定 tuple(给 prometheus Counter/Gauge/Histogram)。"""
    if not labels:
        return (name,)
    return (name,) + tuple(sorted(labels.items()))


class Metrics:
    """
    双后端指标收集器:
      - 安装 prometheus_client: 直接走 Counter/Gauge/Histogram 全局 registry
      - 未安装: 走内存字典 + JSON snapshot(向后兼容,用于 CI 与 mock 环境)

    所有方法签名兼容过去,业务代码无需修改。
    """

    def __init__(self) -> None:
        self.use_prometheus = PROMETHEUS_AVAILABLE
        if self.use_prometheus:
            self._registry = CollectorRegistry()
            self._counters: dict[tuple, Any] = {}
            self._gauges: dict[tuple, Any] = {}
            self._histograms: dict[tuple, Any] = {}
            logger.info("metrics.backend", backend="prometheus_client")
        else:
            # 内存 fallback
            self._registry = None
            self._counters = {}  # type: ignore[assignment]
            self._gauges = {}  # type: ignore[assignment]
            self._histograms = {}  # type: ignore[assignment]
            self._hist_values: dict[tuple, list[float]] = {}  # for fallback
            logger.info("metrics.backend", backend="in_memory")

    def _get_or_create_counter(self, name: str, labels: dict | None) -> Any:
        key = _make_prometheus_label_key(name, labels)
        if key in self._counters:
            return self._counters[key]
        labelnames = list(labels.keys()) if labels else []
        c = Counter(name, name, labelnames=labelnames, registry=self._registry)
        self._counters[key] = c
        return c

    def _get_or_create_gauge(self, name: str, labels: dict | None) -> Any:
        key = _make_prometheus_label_key(name, labels)
        if key in self._gauges:
            return self._gauges[key]
        labelnames = list(labels.keys()) if labels else []
        g = Gauge(name, name, labelnames=labelnames, registry=self._registry)
        self._gauges[key] = g
        return g

    def _get_or_create_histogram(self, name: str, labels: dict | None) -> Any:
        key = _make_prometheus_label_key(name, labels)
        if key in self._histograms:
            return self._histograms[key]
        labelnames = list(labels.keys()) if labels else []
        h = Histogram(name, name, labelnames=labelnames, registry=self._registry)
        self._histograms[key] = h
        return h

    def increment(self, name: str, value: int = 1, labels: dict | None = None) -> None:
        if self.use_prometheus:
            counter = self._get_or_create_counter(name, labels)
            if labels:
                counter.labels(**labels).inc(value)
            else:
                counter.inc(value)
        else:
            key = _make_prometheus_label_key(name, labels)
            self._counters[key] = self._counters.get(key, 0) + value  # type: ignore[assignment]
            logger.debug("metric.counter", name=name, value=value, labels=labels)

    def gauge(self, name: str, value: float, labels: dict | None = None) -> None:
        if self.use_prometheus:
            g = self._get_or_create_gauge(name, labels)
            if labels:
                g.labels(**labels).set(value)
            else:
                g.set(value)
        else:
            key = _make_prometheus_label_key(name, labels)
            self._gauges[key] = value  # type: ignore[assignment]
            logger.debug("metric.gauge", name=name, value=value, labels=labels)

    def observe(self, name: str, value: float, labels: dict | None = None) -> None:
        if self.use_prometheus:
            h = self._get_or_create_histogram(name, labels)
            if labels:
                h.labels(**labels).observe(value)
            else:
                h.observe(value)
        else:
            key = _make_prometheus_label_key(name, labels)
            self._hist_values.setdefault(key, []).append(value)  # type: ignore[attr-defined]
            logger.debug("metric.histogram", name=name, value=value, labels=labels)

    def snapshot(self) -> dict:
        """JSON 快照(向后兼容 /memory fallback)。"""
        if self.use_prometheus:
            # 走 prometheus_client 时 prefer 用 render() 输出 Prometheus text
            return {"backend": "prometheus_client", "registry": str(self._registry)}

        return {
            "backend": "in_memory",
            "counters": dict(self._counters),  # type: ignore[arg-type]
            "gauges": dict(self._gauges),  # type: ignore[arg-type]
            "histograms": {
                k: {
                    "count": len(v),
                    "sum": sum(v),
                    "avg": sum(v) / len(v) if v else 0,
                }
                for k, v in self._hist_values.items()  # type: ignore[union-attr]
            },
        }

    def render_prometheus(self) -> bytes:
        """输出 Prometheus exposition 格式(若安装了 prometheus_client)。"""
        if not self.use_prometheus:
            return b"# metrics backend = in_memory\n# use_prometheus_client = False\n"
        return generate_latest(self._registry)

    @property
    def content_type(self) -> str:
        return CONTENT_TYPE_LATEST


# 全局指标
metrics = Metrics()


_initialized = False


def init_tracing(service_name: str = "content-factory") -> bool:
    """
    初始化 OpenTelemetry 追踪。

    优先级:
      1. CF_TRACE_OTLP=1 → OTLP HTTP exporter(CF_TRACE_OTLP_ENDPOINT 可覆盖)
      2. CF_TRACE_CONSOLE=1 → ConsoleSpanExporter(调试)
      3. 默认只启用 TracerProvider(无导出器,不污染 stdout)

    Returns:
        True  → 初始化成功(含 OTLP/CONSOLE 任意一个)
        False → 降级模式(没装 opentelemetry)
    """
    global _initialized
    if _initialized:
        return True

    if not OTEL_AVAILABLE:
        logger.info("telemetry.fallback", reason="opentelemetry not installed")
        return False

    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)

    # ── OTLP HTTP 导出器 ──
    if os.getenv("CF_TRACE_OTLP"):
        if OTLP_HTTP_AVAILABLE:
            endpoint = os.getenv("CF_TRACE_OTLP_ENDPOINT", "http://localhost:4318/v1/traces")
            try:
                processor = BatchSpanProcessor(HTTPOTLPSpanExporter(endpoint=endpoint))
                provider.add_span_processor(processor)
                logger.info(
                    "telemetry.otlp.enabled",
                    endpoint=endpoint,
                    service=service_name,
                )
            except Exception as e:
                logger.warning("telemetry.otlp.init_failed", error=str(e))
        else:
            logger.warning(
                "telemetry.otlp.missing",
                hint="pip install opentelemetry-exporter-otlp",
            )

    # ── Console 导出器(调试)───
    if os.getenv("CF_TRACE_CONSOLE"):
        try:
            processor = BatchSpanProcessor(ConsoleSpanExporter())
            provider.add_span_processor(processor)
            logger.info("telemetry.console.enabled", service=service_name)
        except Exception:
            pass  # pytest 等环境下 stdout 可能被捕获

    trace.set_tracer_provider(provider)
    _initialized = True
    logger.info("telemetry.initialized", service=service_name)
    return True


@contextmanager
def trace_span(name: str, attributes: dict[str, Any] | None = None) -> Generator:
    """
    追踪一个代码段。

    兼容三种模式:
      1. OpenTelemetry 已初始化: 走 OTel span
      2. OpenTelemetry 未安装: 走 structlog + 内部 metrics 记录 span.duration
    """
    start_time = time.time()

    if OTEL_AVAILABLE and _initialized:
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
        # 降级模式: structlog + 内存指标
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
    metrics.increment(
        "workflow.runs.total",
        labels={
            "tenant": tenant_id,
            "editor": editor_slug,
            "status": status,
        },
    )
    metrics.observe(
        "workflow.runs.duration",
        duration_seconds,
        labels={
            "tenant": tenant_id,
            "editor": editor_slug,
        },
    )
    metrics.increment(
        "workflow.compliance.passed" if compliance_passed else "workflow.compliance.failed"
    )


def get_metrics_snapshot() -> dict:
    """JSON 快照(向后兼容 / 由 FastAPI /metrics 路由选择调用 render 或 snapshot)"""
    return metrics.snapshot()


def render_metrics_prometheus() -> bytes:
    """Prometheus exposition 格式(/metrics 端点实际使用)"""
    return metrics.render_prometheus()


def metrics_content_type() -> str:
    """Prometheus exposition content-type"""
    return metrics.content_type
