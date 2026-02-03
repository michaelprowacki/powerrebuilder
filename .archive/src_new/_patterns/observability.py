"""Observability Framework - OpenTelemetry integration for distributed tracing.

This module provides comprehensive observability features including distributed
tracing, metrics collection, and performance monitoring for the pipeline.
"""

import logging
import time
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Union

try:
    from opentelemetry import trace, metrics
    from opentelemetry.exporter.jaeger.thrift import JaegerExporter
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.exporter.prometheus import PrometheusMetricReader
    from opentelemetry.metrics import get_meter_provider, set_meter_provider
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.resources import Resource, SERVICE_NAME
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.trace import get_tracer_provider, set_tracer_provider

    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    trace = None
    metrics = None

logger = logging.getLogger(__name__)


class ObservabilityBackend(str, Enum):
    """Supported observability backends."""

    NONE = "none"
    CONSOLE = "console"
    JAEGER = "jaeger"
    OTLP = "otlp"
    PROMETHEUS = "prometheus"
    DATADOG = "datadog"


@dataclass
class TraceContext:
    """Trace context information."""

    trace_id: str
    span_id: str
    parent_span_id: Optional[str] = None
    baggage: Dict[str, Any] = None

    def __post_init__(self):
        if self.baggage is None:
            self.baggage = {}


@dataclass
class MetricPoint:
    """Single metric data point."""

    name: str
    value: float
    timestamp: datetime
    labels: Dict[str, str]
    metric_type: str  # counter, gauge, histogram


@dataclass
class SpanInfo:
    """Information about a trace span."""

    name: str
    start_time: float
    end_time: Optional[float] = None
    attributes: Dict[str, Any] = None
    status: str = "ok"
    error_message: Optional[str] = None

    def __post_init__(self):
        if self.attributes is None:
            self.attributes = {}

    @property
    def duration(self) -> float:
        """Get span duration in seconds."""
        if self.end_time is None:
            return 0.0
        return self.end_time - self.start_time


class ObservabilityManager:
    """Manages observability for the pipeline."""

    def __init__(
        self,
        service_name: str = "powerrebuilder",
        backend: ObservabilityBackend = ObservabilityBackend.NONE,
        endpoint: Optional[str] = None,
    ):
        """Initialize observability manager.

        Args:
            service_name: Name of the service
            backend: Observability backend to use
            endpoint: Backend endpoint URL
        """
        self.service_name = service_name
        self.backend = backend
        self.endpoint = endpoint
        self.tracer = None
        self.meter = None

        if OTEL_AVAILABLE and backend != ObservabilityBackend.NONE:
            self._initialize_telemetry()

    def _initialize_telemetry(self) -> None:
        """Initialize OpenTelemetry providers."""
        # Create resource
        resource = Resource.create(
            {
                SERVICE_NAME: self.service_name,
                "service.version": "1.0.0",
                "deployment.environment": "production",
            }
        )

        # Initialize tracing
        if self.backend in [ObservabilityBackend.JAEGER, ObservabilityBackend.OTLP]:
            trace_provider = TracerProvider(resource=resource)

            if self.backend == ObservabilityBackend.JAEGER:
                exporter = JaegerExporter(
                    agent_host_name=self.endpoint or "localhost",
                    agent_port=6831,
                )
            else:  # OTLP
                exporter = OTLPSpanExporter(
                    endpoint=self.endpoint or "localhost:4317",
                    insecure=True,
                )

            trace_provider.add_span_processor(BatchSpanProcessor(exporter))
            set_tracer_provider(trace_provider)
            self.tracer = trace.get_tracer(__name__)

        # Initialize metrics
        if self.backend == ObservabilityBackend.PROMETHEUS:
            reader = PrometheusMetricReader()
            meter_provider = MeterProvider(resource=resource, metric_readers=[reader])
            set_meter_provider(meter_provider)
            self.meter = metrics.get_meter(__name__)

    @contextmanager
    def trace_span(
        self,
        name: str,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> Iterator[Any]:
        """Create a trace span.

        Args:
            name: Span name
            attributes: Span attributes

        Yields:
            Span object or None
        """
        if self.tracer and OTEL_AVAILABLE:
            with self.tracer.start_as_current_span(name) as span:
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, value)
                yield span
        else:
            # No-op when tracing is disabled
            yield None

    def record_metric(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
        metric_type: str = "gauge",
    ) -> None:
        """Record a metric value.

        Args:
            name: Metric name
            value: Metric value
            labels: Metric labels
            metric_type: Type of metric
        """
        if self.meter and OTEL_AVAILABLE:
            if metric_type == "counter":
                counter = self.meter.create_counter(name)
                counter.add(value, labels or {})
            elif metric_type == "histogram":
                histogram = self.meter.create_histogram(name)
                histogram.record(value, labels or {})
            else:  # gauge
                gauge = self.meter.create_up_down_counter(name)
                gauge.add(value, labels or {})

        # Also log metrics when telemetry is disabled
        logger.debug(
            "Metric: %s=%s (type=%s, labels=%s)",
            name,
            value,
            metric_type,
            labels,
        )

    @contextmanager
    def measure_duration(
        self,
        metric_name: str,
        labels: Optional[Dict[str, str]] = None,
    ) -> Iterator[None]:
        """Measure and record duration of an operation.

        Args:
            metric_name: Name of the duration metric
            labels: Metric labels

        Yields:
            None
        """
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            self.record_metric(
                f"{metric_name}_duration_seconds",
                duration,
                labels,
                "histogram",
            )


class PipelineTracer:
    """Specialized tracer for pipeline operations."""

    def __init__(self, observability: ObservabilityManager):
        """Initialize pipeline tracer.

        Args:
            observability: Observability manager instance
        """
        self.observability = observability
        self.stage_spans: Dict[str, Any] = {}

    @contextmanager
    def trace_stage(
        self,
        stage: str,
        input_path: Path,
        output_path: Path,
    ) -> Iterator[None]:
        """Trace a pipeline stage.

        Args:
            stage: Stage name
            input_path: Input path
            output_path: Output path

        Yields:
            None
        """
        attributes = {
            "pipeline.stage": stage,
            "input.path": str(input_path),
            "output.path": str(output_path),
        }

        with self.observability.trace_span(
            f"pipeline.{stage}",
            attributes,
        ) as span:
            self.stage_spans[stage] = span

            # Record stage start metric
            self.observability.record_metric(
                "pipeline_stage_started",
                1,
                {"stage": stage},
                "counter",
            )

            try:
                yield

                # Record stage success
                self.observability.record_metric(
                    "pipeline_stage_completed",
                    1,
                    {"stage": stage, "status": "success"},
                    "counter",
                )
            except Exception as e:
                # Record stage failure
                self.observability.record_metric(
                    "pipeline_stage_completed",
                    1,
                    {"stage": stage, "status": "failure"},
                    "counter",
                )

                if span and OTEL_AVAILABLE:
                    span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                raise

    @contextmanager
    def trace_file_processing(
        self,
        file_path: Path,
        operation: str,
    ) -> Iterator[None]:
        """Trace file processing.

        Args:
            file_path: File being processed
            operation: Operation being performed

        Yields:
            None
        """
        attributes = {
            "file.path": str(file_path),
            "file.name": file_path.name,
            "file.extension": file_path.suffix,
            "file.size": file_path.stat().st_size if file_path.exists() else 0,
            "operation": operation,
        }

        with self.observability.trace_span(
            f"process_file.{operation}",
            attributes,
        ):
            yield


class MetricsCollector:
    """Collects and aggregates pipeline metrics."""

    def __init__(self, observability: ObservabilityManager):
        """Initialize metrics collector.

        Args:
            observability: Observability manager instance
        """
        self.observability = observability
        self.counters: Dict[str, int] = {}
        self.gauges: Dict[str, float] = {}
        self.histograms: Dict[str, List[float]] = {}

    def increment_counter(
        self,
        name: str,
        value: int = 1,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """Increment a counter metric.

        Args:
            name: Counter name
            value: Increment value
            labels: Metric labels
        """
        key = f"{name}:{labels}" if labels else name
        self.counters[key] = self.counters.get(key, 0) + value

        self.observability.record_metric(name, value, labels, "counter")

    def set_gauge(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """Set a gauge metric.

        Args:
            name: Gauge name
            value: Gauge value
            labels: Metric labels
        """
        key = f"{name}:{labels}" if labels else name
        self.gauges[key] = value

        self.observability.record_metric(name, value, labels, "gauge")

    def record_histogram(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """Record a histogram value.

        Args:
            name: Histogram name
            value: Value to record
            labels: Metric labels
        """
        key = f"{name}:{labels}" if labels else name
        if key not in self.histograms:
            self.histograms[key] = []
        self.histograms[key].append(value)

        self.observability.record_metric(name, value, labels, "histogram")

    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary.

        Returns:
            Metrics summary dictionary
        """
        return {
            "counters": dict(self.counters),
            "gauges": dict(self.gauges),
            "histogram_counts": {k: len(v) for k, v in self.histograms.items()},
        }


# Singleton instances
_observability: Optional[ObservabilityManager] = None
_tracer: Optional[PipelineTracer] = None
_metrics: Optional[MetricsCollector] = None


def initialize_observability(
    service_name: str = "powerrebuilder",
    backend: Union[str, ObservabilityBackend] = ObservabilityBackend.NONE,
    endpoint: Optional[str] = None,
) -> None:
    """Initialize global observability.

    Args:
        service_name: Service name
        backend: Backend type
        endpoint: Backend endpoint
    """
    global _observability, _tracer, _metrics

    if isinstance(backend, str):
        backend = ObservabilityBackend(backend)

    _observability = ObservabilityManager(service_name, backend, endpoint)
    _tracer = PipelineTracer(_observability)
    _metrics = MetricsCollector(_observability)

    logger.info(
        "Observability initialized: backend=%s, endpoint=%s",
        backend,
        endpoint,
    )


def get_observability() -> ObservabilityManager:
    """Get global observability manager.

    Returns:
        Observability manager instance
    """
    global _observability
    if _observability is None:
        initialize_observability()
    return _observability


def get_tracer() -> PipelineTracer:
    """Get global pipeline tracer.

    Returns:
        Pipeline tracer instance
    """
    global _tracer
    if _tracer is None:
        initialize_observability()
    return _tracer


def get_metrics() -> MetricsCollector:
    """Get global metrics collector.

    Returns:
        Metrics collector instance
    """
    global _metrics
    if _metrics is None:
        initialize_observability()
    return _metrics
