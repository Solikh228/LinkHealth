"""
OpenTelemetry Instrumentation for SubTracker FastAPI Backend.

Configures OTLP metrics, traces, and structured logging export to an OpenTelemetry
Collector or compatible backend (Prometheus, Loki, Tempo).
"""

import logging
import os
import re
from typing import Optional

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


def extract_service_version() -> str:
    """Extract service version from APP_IMAGE environment variable or fallback to version."""
    app_image = os.getenv("APP_IMAGE", "").strip()
    if app_image:
        # Match tag following the last colon
        if ":" in app_image:
            tag = app_image.split(":")[-1]
            if tag:
                return tag
    return os.getenv("SERVICE_VERSION", os.getenv("OTEL_SERVICE_VERSION", "1.0.0"))


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
        # If app or engine provided after initial setup, instrument them
        if app is not None and not getattr(app.state, "_otel_instrumented", False):
            FastAPIInstrumentor.instrument_app(app)
            app.state._otel_instrumented = True
        if engine is not None:
            try:
                SQLAlchemyInstrumentor().instrument(engine=engine, skip_dep_check=True)
            except Exception as e:
                logger.debug(f"SQLAlchemy already instrumented or exception: {e}")
        return

    # Check if OpenTelemetry SDK is explicitly disabled (e.g. for lightweight CLI or tests)
    if os.getenv("OTEL_SDK_DISABLED", "false").lower() in ("true", "1", "yes"):
        logger.info("OpenTelemetry SDK disabled via OTEL_SDK_DISABLED")
        _telemetry_initialized = True
        return

    resource = get_resource()
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    protocol = os.getenv("OTEL_EXPORTER_OTLP_PROTOCOL", "").lower()

    # Determine whether to use HTTP or gRPC exporter
    is_http = (
        protocol in ("http", "http/protobuf", "http/json")
        or ":4318" in endpoint
        or endpoint.endswith("/v1/traces")
    )

    try:
        if is_http:
            # OTLP over HTTP
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
            # OTLP over gRPC (default port 4317)
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter as GrpcSpanExporter
            from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter as GrpcMetricExporter
            from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter as GrpcLogExporter

            # Clean endpoint for gRPC (strip http:// or https:// prefix)
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

        # Attach OpenTelemetry LoggingHandler to root logger
        log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
        log_level = getattr(logging, log_level_str, logging.INFO)
        otel_handler = LoggingHandler(level=log_level, logger_provider=logger_provider)
        logging.getLogger().addHandler(otel_handler)

        # Auto-instrument logging to inject trace and span IDs into log format
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
