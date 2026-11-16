"""
OpenTelemetry Instrumentation for SubTracker FastAPI Backend.

Configures OTLP metrics, traces, structured logging export, and custom business metrics
for SubTracker subscriptions, active users, and renewal notifications.
"""

import logging
import os
import re
import time
from typing import Any, Dict, Optional

from fastapi import FastAPI
from sqlalchemy.engine import Engine

from opentelemetry import metrics, trace, _logs
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader, MetricExporter
from opentelemetry.sdk._logs import LoggerProvider
try:
    from opentelemetry.instrumentation.logging.handler import LoggingHandler
except ImportError:
    from opentelemetry.sdk._logs import LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor, LogExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor

logger = logging.getLogger("subtracker.telemetry")

_telemetry_initialized = False

# Meter for custom application business metrics
meter = metrics.get_meter("subtracker.business.metrics", "1.0.0")

# 1. Counter: subscriptions_created
subscriptions_created_counter = meter.create_counter(
    name="subscriptions_created",
    description="Total number of subscriptions created",
    unit="1",
)

# 2. UpDownCounter / Gauge: active_subscriptions
active_subscriptions_counter = meter.create_up_down_counter(
    name="active_subscriptions",
    description="Current total number of active subscriptions",
    unit="1",
)

# 3. UpDownCounter / Gauge: active_users
active_users_counter = meter.create_up_down_counter(
    name="active_users",
    description="Current total number of active users",
    unit="1",
)

# 4. Counter: subscription_creation_failures
subscription_creation_failures_counter = meter.create_counter(
    name="subscription_creation_failures",
    description="Total number of failed subscription creation or update attempts",
    unit="1",
)

# 5. Histogram: notification_delivery_latency
notification_delivery_latency_histogram = meter.create_histogram(
    name="notification_delivery_latency",
    description="Latency of sending or processing subscription renewal notifications",
    unit="ms",
)


def extract_service_version() -> str:
    """Extract service version from APP_IMAGE environment variable or fallback to version."""
    app_image = os.getenv("APP_IMAGE", "").strip()
    if app_image:
        if ":" in app_image:
            tag = app_image.split(":")[-1]
            if tag:
                return tag
    return os.getenv("SERVICE_VERSION", os.getenv("OTEL_SERVICE_VERSION", "1.0.0"))


def get_metric_labels(extra: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
    """
    Construct standardized metric labels ensuring all metrics include 'environment'
    (from deployment.environment.name) and 'deployed_version' (from service.version).
    """
    labels = {
        "environment": os.getenv("DEPLOYMENT_ENVIRONMENT", os.getenv("ENVIRONMENT", "dev")).lower(),
        "deployed_version": extract_service_version(),
    }
    if extra:
        for k, v in extra.items():
            if v is not None:
                labels[k] = str(v)
    return labels


def record_subscription_created(
    cadence: str = "monthly",
    vendor: str = "",
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    """Record creation of a new subscription."""
    try:
        data = {"cadence": cadence}
        if vendor:
            data["vendor"] = vendor
        if extra:
            data.update(extra)
        attrs = get_metric_labels(data)
        subscriptions_created_counter.add(1, attrs)
        active_subscriptions_counter.add(1, attrs)
        logger.debug(f"Metric recorded: subscriptions_created (+1), active_subscriptions (+1)")
    except Exception as e:
        logger.debug(f"Failed to record subscription created metric: {e}")


def record_active_subscriptions_delta(
    delta: int,
    status: str = "active",
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    """Update active subscriptions gauge/counter with positive or negative delta."""
    try:
        data = {"status": status}
        if extra:
            data.update(extra)
        attrs = get_metric_labels(data)
        active_subscriptions_counter.add(delta, attrs)
        logger.debug(f"Metric recorded: active_subscriptions ({delta:+d})")
    except Exception as e:
        logger.debug(f"Failed to record active subscriptions delta: {e}")


def record_active_user_login(user_id: str = "", extra: Optional[Dict[str, Any]] = None) -> None:
    """Record an active user session login."""
    try:
        data = {}
        if user_id:
            data["user_id"] = user_id
        if extra:
            data.update(extra)
        attrs = get_metric_labels(data)
        active_users_counter.add(1, attrs)
        logger.debug("Metric recorded: active_users (+1)")
    except Exception as e:
        logger.debug(f"Failed to record active user login: {e}")


def record_active_user_logout(user_id: str = "", extra: Optional[Dict[str, Any]] = None) -> None:
    """Record user session logout or account deletion."""
    try:
        data = {}
        if user_id:
            data["user_id"] = user_id
        if extra:
            data.update(extra)
        attrs = get_metric_labels(data)
        active_users_counter.add(-1, attrs)
        logger.debug("Metric recorded: active_users (-1)")
    except Exception as e:
        logger.debug(f"Failed to record active user logout: {e}")


def record_subscription_failure(
    reason: str = "validation_error",
    operation: str = "create",
    status_code: int = 400,
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    """Record failed subscription creation or update attempt."""
    try:
        data = {
            "reason": reason,
            "operation": operation,
            "status_code": str(status_code),
        }
        if extra:
            data.update(extra)
        attrs = get_metric_labels(data)
        subscription_creation_failures_counter.add(1, attrs)
        logger.debug(f"Metric recorded: subscription_creation_failures (+1, reason={reason})")
    except Exception as e:
        logger.debug(f"Failed to record subscription failure metric: {e}")


def record_notification_latency(
    duration_ms: float,
    notification_type: str = "renewal_reminder",
    status: str = "delivered",
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    """Record latency of delivering subscription renewal notification in milliseconds."""
    try:
        data = {
            "notification_type": notification_type,
            "status": status,
        }
        if extra:
            data.update(extra)
        attrs = get_metric_labels(data)
        notification_delivery_latency_histogram.record(duration_ms, attrs)
        logger.debug(f"Metric recorded: notification_delivery_latency ({duration_ms:.2f} ms)")
    except Exception as e:
        logger.debug(f"Failed to record notification latency: {e}")


def get_resource() -> Resource:
    """Construct OpenTelemetry Resource with service attributes."""
    service_name = os.getenv("OTEL_SERVICE_NAME", os.getenv("SERVICE_NAME", "subtracker-backend"))
    deployment_env = os.getenv("DEPLOYMENT_ENVIRONMENT", os.getenv("ENVIRONMENT", "dev")).lower()
    service_version = extract_service_version()

    attributes = {
        "service.name": service_name,
        "deployment.environment.name": deployment_env,
        "deployment.environment": deployment_env,
        "service.version": service_version,
    }

    return Resource.create(attributes)


def init_telemetry(app: Optional[FastAPI] = None, engine: Optional[Engine] = None) -> None:
    """
    Initialize OpenTelemetry Tracing, Metrics, Logging, and Auto-instrumentation.
    Supports both gRPC and HTTP OTLP export protocols based on configuration.
    """
    global _telemetry_initialized
    if _telemetry_initialized:
        if app is not None and not getattr(app.state, "_otel_instrumented", False):
            FastAPIInstrumentor.instrument_app(app)
            app.state._otel_instrumented = True
        if engine is not None:
            try:
                SQLAlchemyInstrumentor().instrument(engine=engine, skip_dep_check=True)
            except Exception as e:
                logger.debug(f"SQLAlchemy already instrumented or exception: {e}")
        return

    if os.getenv("OTEL_SDK_DISABLED", "false").lower() in ("true", "1", "yes"):
        logger.info("OpenTelemetry SDK disabled via OTEL_SDK_DISABLED")
        _telemetry_initialized = True
        return

    resource = get_resource()
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    protocol = os.getenv("OTEL_EXPORTER_OTLP_PROTOCOL", "").lower()

    is_http = (
        protocol in ("http", "http/protobuf", "http/json")
        or ":4318" in endpoint
        or endpoint.endswith("/v1/traces")
    )

    try:
        if is_http:
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter as HttpSpanExporter
            from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter as HttpMetricExporter
            from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter as HttpLogExporter

            traces_endpoint = endpoint if endpoint.endswith("/v1/traces") else f"{endpoint.rstrip('/')}/v1/traces"
            metrics_endpoint = endpoint if endpoint.endswith("/v1/metrics") else f"{endpoint.rstrip('/')}/v1/metrics"
            logs_endpoint = endpoint if endpoint.endswith("/v1/logs") else f"{endpoint.rstrip('/')}/v1/logs"

            span_exporter: SpanExporter = HttpSpanExporter(endpoint=traces_endpoint)
            metric_exporter: MetricExporter = HttpMetricExporter(endpoint=metrics_endpoint)
            log_exporter: LogExporter = HttpLogExporter(endpoint=logs_endpoint)
        else:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter as GrpcSpanExporter
            from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter as GrpcMetricExporter
            from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter as GrpcLogExporter

            insecure = not endpoint.startswith("https://")
            clean_endpoint = re.sub(r"^https?://", "", endpoint)

            span_exporter = GrpcSpanExporter(endpoint=clean_endpoint, insecure=insecure)
            metric_exporter = GrpcMetricExporter(endpoint=clean_endpoint, insecure=insecure)
            log_exporter = GrpcLogExporter(endpoint=clean_endpoint, insecure=insecure)

        # 1. Tracing Setup
        tracer_provider = TracerProvider(resource=resource)
        span_processor = BatchSpanProcessor(span_exporter)
        tracer_provider.add_span_processor(span_processor)
        trace.set_tracer_provider(tracer_provider)

        # 2. Metrics Setup
        metric_reader = PeriodicExportingMetricReader(
            metric_exporter,
            export_interval_millis=int(os.getenv("OTEL_METRIC_EXPORT_INTERVAL_MS", "15000")),
        )
        meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
        metrics.set_meter_provider(meter_provider)

        # 3. Logging Setup
        logger_provider = LoggerProvider(resource=resource)
        log_processor = BatchLogRecordProcessor(log_exporter)
        logger_provider.add_log_record_processor(log_processor)
        _logs.set_logger_provider(logger_provider)

        log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
        log_level = getattr(logging, log_level_str, logging.INFO)
        otel_handler = LoggingHandler(level=log_level, logger_provider=logger_provider)
        logging.getLogger().addHandler(otel_handler)

        LoggingInstrumentor().instrument(set_logging_format=True)

        # 4. Auto-instrument SQLAlchemy
        try:
            if engine is not None:
                SQLAlchemyInstrumentor().instrument(engine=engine, skip_dep_check=True)
            else:
                SQLAlchemyInstrumentor().instrument(skip_dep_check=True)
            logger.info("SQLAlchemy OpenTelemetry auto-instrumentation enabled")
        except Exception as sqla_err:
            logger.warning(f"Could not instrument SQLAlchemy: {sqla_err}")

        # 5. Auto-instrument FastAPI app
        if app is not None:
            FastAPIInstrumentor.instrument_app(
                app,
                tracer_provider=tracer_provider,
                meter_provider=meter_provider,
            )
            app.state._otel_instrumented = True
            logger.info("FastAPI OpenTelemetry auto-instrumentation enabled")

        _telemetry_initialized = True
        logger.info(
            f"OpenTelemetry initialized for {resource.attributes.get('service.name')} "
            f"(env={resource.attributes.get('deployment.environment.name')}, "
            f"version={resource.attributes.get('service.version')}) -> {endpoint}"
        )

    except Exception as err:
        logger.warning(f"OpenTelemetry initialization failed (running in fallback mode): {err}")
        _telemetry_initialized = True
