# SubTracker Observability Stack (OpenTelemetry + Prometheus + Loki + Tempo + Grafana)

This directory contains the standalone observability infrastructure for SubTracker.
It operates independently from the application stack (`docker-compose.prod.yml`), enabling both `subtracker-dev` and `subtracker-prod` instances to route their metrics, logs, and traces into a centralized observability backend.

---

## Architecture Overview

```
                      ┌───────────────────────────────────────┐
                      │    FastAPI Application Containers     │
                      │  (subtracker-dev / subtracker-prod)   │
                      │   - OpenTelemetry Python SDK          │
                      │   - FastAPI & SQLAlchemy auto-instr   │
                      │   - Structured logging handler        │
                      │   - Custom business metrics           │
                      └──────────────────┬────────────────────┘
                                         │ OTLP (gRPC / HTTP)
                                         ▼
                 ┌─────────────────────────────────────────────────┐
                 │       OpenTelemetry Collector (port 4317/4318)   │
                 └───────┬─────────────────┬─────────────────┬─────┘
                         │ Metrics         │ Logs            │ Traces
                         ▼                 ▼                 ▼
                  ┌────────────┐    ┌────────────┐    ┌────────────┐
                  │ Prometheus │    │    Loki    │    │   Tempo    │
                  │ (Metrics)  │    │   (Logs)   │    │  (Traces)  │
                  └──────┬─────┘    └──────┬─────┘    └──────┬─────┘
                         │                 │                 │
                         └─────────────────┼─────────────────┘
                                           ▼
                                 ┌───────────────────┐
                                 │      Grafana      │
                                 │    (Port 3000)    │
                                 └───────────────────┘
```

---

## Custom Application Business Metrics

The FastAPI backend exposes the following custom OpenTelemetry business metrics:

| Metric Name | Type | Description | Labels / Attributes |
| :--- | :--- | :--- | :--- |
| `subscriptions_created` | Counter | Total number of subscriptions created | `environment`, `deployed_version`, `cadence`, `vendor` |
| `active_subscriptions` | UpDownCounter / Gauge | Current total number of active subscriptions | `environment`, `deployed_version`, `status` |
| `active_users` | UpDownCounter / Gauge | Current total number of active users | `environment`, `deployed_version`, `user_id` |
| `subscription_creation_failures` | Counter | Total failed creation/update attempts (validation, DB, 5xx) | `environment`, `deployed_version`, `reason`, `operation`, `status_code` |
| `notification_delivery_latency` | Histogram | Latency (in ms) of sending/processing renewal notifications | `environment`, `deployed_version`, `notification_type`, `status` |

---

## Services & Ports

| Service | Port | Description |
| :--- | :--- | :--- |
| **OpenTelemetry Collector** | `4317` (gRPC), `4318` (HTTP) | Central telemetry receiver and router |
| **OTel Collector Diagnostics** | `8888` (Internal), `8889` (Prometheus) | Diagnostics and Prometheus scrape endpoint |
| **Prometheus** | `9090` | Time-series metrics storage and querying |
| **Loki** | `3100` | Log aggregation with native OTLP ingestion |
| **Tempo** | `3200` (HTTP Query), `4317` (Internal) | Distributed tracing backend |
| **Grafana** | `3000` | Pre-provisioned dashboards with unified metrics/logs/traces |

---

## Quickstart

### 1. Launch Observability Stack
```bash
cd observability
docker compose up -d
```

### 2. Access Grafana UI
Open your browser to: [http://localhost:3000](http://localhost:3000)
- **User**: `admin`
- **Password**: `admin`
- Pre-provisioned Datasources: `Prometheus`, `Loki`, `Tempo`
- Pre-provisioned Dashboard: `SubTracker - OpenTelemetry Observability` (with `environment` and `deployed_version` template variables)

### 3. Connect Application (`subtracker-dev` or `subtracker-prod`)
Set the following environment variables in your application's `.env`:
```ini
OTEL_SERVICE_NAME=subtracker-backend
OTEL_EXPORTER_OTLP_ENDPOINT=http://<OBSERVABILITY_HOST>:4317
OTEL_EXPORTER_OTLP_PROTOCOL=grpc
DEPLOYMENT_ENVIRONMENT=dev # or "prod"
APP_IMAGE=subtracker:20261116-120000-abc1234
```
The FastAPI backend will automatically export all traces, metrics, and structured logs to the collector.
