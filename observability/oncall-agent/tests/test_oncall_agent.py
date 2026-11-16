import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import GrafanaAlertItem, GrafanaAlertPayload, RCAReport, TelemetryContext
from app.telemetry_client import TelemetryClient
from app.llm_engine import LLMEngine
from app.publisher import IncidentPublisher


client = TestClient(app)


def test_grafana_payload_parsing():
    sample_payload = {
        "receiver": "subtracker-oncall-webhook",
        "status": "firing",
        "alerts": [
            {
                "status": "firing",
                "labels": {
                    "alertname": "HighSubscriptionCreationFailureRate",
                    "service": "subtracker-backend",
                    "environment": "prod",
                    "deployed_version": "20261116-150000-abc1234",
                    "severity": "critical",
                    "owner": "subtracker-oncall",
                },
                "annotations": {
                    "summary": "High subscription creation failure rate on subtracker-backend (prod)",
                    "description": "Subscription creation failure rate is 5.2 failures/min.",
                    "dashboard_url": "http://localhost:3000/d/subtracker-overview",
                    "runbook_url": "https://github.com/Solikh228/LinkHealth/runbook.md",
                },
                "startsAt": "2026-11-16T15:00:00Z",
            }
        ],
        "groupLabels": {"alertname": "HighSubscriptionCreationFailureRate"},
        "commonLabels": {"service": "subtracker-backend"},
        "commonAnnotations": {"summary": "High failure rate"},
    }

    payload_model = GrafanaAlertPayload.model_validate(sample_payload)
    assert payload_model.status == "firing"
    assert len(payload_model.alerts) == 1
    alert = payload_model.alerts[0]
    assert alert.labels["alertname"] == "HighSubscriptionCreationFailureRate"
    assert alert.labels["environment"] == "prod"
    assert alert.labels["deployed_version"] == "20261116-150000-abc1234"
    assert "failures/min" in alert.annotations["description"]


@pytest.mark.anyio
async def test_telemetry_client_mocked():
    tel_client = TelemetryClient(
        loki_url="http://loki-mock:3100",
        tempo_url="http://tempo-mock:3200",
        prometheus_url="http://prometheus-mock:9090",
    )

    alert = GrafanaAlertItem(
        status="firing",
        labels={
            "alertname": "HighSubscriptionCreationFailureRate",
            "service": "subtracker-backend",
            "environment": "dev",
            "deployed_version": "20261116-140000-sha123",
        },
        annotations={
            "summary": "Elevated failures",
            "description": "Rate > 3/m",
        },
    )

    mock_loki_resp = MagicMock()
    mock_loki_resp.status_code = 200
    mock_loki_resp.json.return_value = {
        "data": {
            "result": [
                {
                    "values": [
                        ["1700000000000000000", "ERROR 2026-11-16: Failed to create subscription: ValidationError: lastChargeDate missing"]
                    ]
                }
            ]
        }
    }

    mock_tempo_resp = MagicMock()
    mock_tempo_resp.status_code = 200
    mock_tempo_resp.json.return_value = {
        "traces": [
            {
                "traceID": "mock-trace-12345",
                "rootServiceName": "subtracker-backend",
                "rootTraceName": "POST /api/subscriptions",
                "durationMs": 420.5,
            }
        ]
    }

    mock_prom_resp = MagicMock()
    mock_prom_resp.status_code = 200
    mock_prom_resp.json.return_value = {
        "data": {
            "result": [{"value": [1700000000, "4.8"]}]
        }
    }

    with patch("httpx.AsyncClient.get") as mock_get:
        def side_effect(url, **kwargs):
            if "3100" in url:
                return mock_loki_resp
            elif "3200" in url:
                return mock_tempo_resp
            elif "9090" in url:
                return mock_prom_resp
            return MagicMock(status_code=404)

        mock_get.side_effect = side_effect

        context = await tel_client.aggregate_context(alert)

        assert context.alertname == "HighSubscriptionCreationFailureRate"
        assert context.service == "subtracker-backend"
        assert context.failure_metric_rate == 4.8
        assert len(context.loki_logs) == 1
        assert "ValidationError" in context.loki_logs[0]
        assert len(context.tempo_traces) == 1
        assert context.tempo_traces[0]["trace_id"] == "mock-trace-12345"


@pytest.mark.anyio
async def test_llm_engine_heuristic_rca():
    engine = LLMEngine()  # No API keys provided -> triggers deterministic heuristic mode

    alert = GrafanaAlertItem(
        status="firing",
        labels={
            "alertname": "HighSubscriptionCreationFailureRate",
            "service": "subtracker-backend",
            "environment": "dev",
            "deployed_version": "20261116-140000-sha123",
            "severity": "critical",
        },
        annotations={
            "summary": "Subscription creation rate elevated",
            "description": "Failure rate is 4.5/min",
            "dashboard_url": "http://localhost:3000/d/subtracker-overview",
            "runbook_url": "http://localhost/runbook.md",
        },
    )

    context = TelemetryContext(
        alertname="HighSubscriptionCreationFailureRate",
        service="subtracker-backend",
        environment="dev",
        deployed_version="20261116-140000-sha123",
        failure_metric_rate=4.5,
        active_subscriptions=42,
        active_users=10,
        loki_logs=["[ERROR] ValidationError: Field required lastChargeDate"],
        tempo_traces=[{"trace_id": "abc1", "root_service": "subtracker-backend"}],
        git_commits=[{"sha": "1234567", "message": "feat: update models", "author": "dev"}],
    )

    rca = await engine.analyze_incident(alert, context)

    assert rca.alertname == "HighSubscriptionCreationFailureRate"
    assert rca.service == "subtracker-backend"
    assert rca.environment == "dev"
    assert rca.severity == "critical"
    assert "validation" in rca.root_cause.lower()
    assert rca.immediate_mitigation
    assert "rollback" in rca.rollback_command.lower() or "docker compose" in rca.rollback_command.lower()
    assert rca.code_patch is not None
    assert len(rca.preventative_actions) > 0


@pytest.mark.anyio
async def test_llm_engine_mock_openai():
    engine = LLMEngine(openai_api_key="sk-mock-test-key")

    alert = GrafanaAlertItem(
        status="firing",
        labels={"alertname": "HighSubscriptionCreationFailureRate", "service": "subtracker-backend", "environment": "prod"},
    )
    context = TelemetryContext(
        alertname="HighSubscriptionCreationFailureRate",
        service="subtracker-backend",
        environment="prod",
        deployed_version="v2",
        failure_metric_rate=6.1,
    )

    mock_response_data = {
        "choices": [
            {
                "message": {
                    "content": json.dumps({
                        "summary": "Database deadlocks causing subscription creation failures",
                        "root_cause": "Concurrent writes on subscriptions table locking user row",
                        "immediate_mitigation": "Increase DB connection timeout and scale worker threads",
                        "rollback_command": "docker compose down && docker compose up -d",
                        "code_patch": "--- a/db.py\n+++ b/db.py\n",
                        "preventative_actions": ["Implement row level locking with SKIP LOCKED"],
                    })
                }
            }
        ]
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = mock_response_data

    with patch("httpx.AsyncClient.post", return_value=mock_resp):
        rca = await engine.analyze_incident(alert, context)
        assert rca.summary == "Database deadlocks causing subscription creation failures"
        assert "Concurrent writes" in rca.root_cause
        assert "SKIP LOCKED" in rca.preventative_actions[0]


@pytest.mark.anyio
async def test_incident_publisher_local_and_github(tmp_path: Path):
    publisher = IncidentPublisher(
        incidents_dir=str(tmp_path),
        github_token="ghp_mock_token",
        github_repository="Solikh228/LinkHealth",
    )

    rca = RCAReport(
        incident_id="inc_test_123",
        alertname="HighSubscriptionCreationFailureRate",
        status="firing",
        service="subtracker-backend",
        environment="prod",
        deployed_version="20261116-abc1234",
        severity="critical",
        summary="High subscription creation failure rate",
        root_cause="Schema validation mismatch",
        evidence_logs=["ERROR: 500 internal server error"],
        evidence_traces=[{"trace_id": "test_trace"}],
        current_metrics={"failure_rate_per_min": 5.0},
        immediate_mitigation="Rollback image",
        rollback_command="docker compose pull && docker compose up -d",
        code_patch="--- diff",
        preventative_actions=["Add schema validation test"],
        dashboard_url="http://grafana/d/overview",
        runbook_url="http://github/runbook",
    )

    # 1. Format markdown test
    markdown = publisher.format_markdown(rca)
    assert "# 🚨 Incident Report: HighSubscriptionCreationFailureRate" in markdown
    assert "Schema validation mismatch" in markdown
    assert "docker compose pull" in markdown
    assert "http://grafana/d/overview" in markdown

    # 2. Local save test
    file_path = publisher.save_local_report(rca)
    assert Path(file_path).exists()
    saved_content = Path(file_path).read_text(encoding="utf-8")
    assert saved_content == markdown

    # 3. GitHub Issue mock test
    mock_gh_resp = MagicMock()
    mock_gh_resp.status_code = 201
    mock_gh_resp.json.return_value = {"html_url": "https://github.com/Solikh228/LinkHealth/issues/99"}

    with patch("httpx.AsyncClient.post", return_value=mock_gh_resp):
        published_rca = await publisher.publish(rca)
        assert published_rca.github_issue_url == "https://github.com/Solikh228/LinkHealth/issues/99"
        assert published_rca.incident_file_path == file_path


def test_api_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "subtracker-oncall-agent"


def test_api_simulate_alert_and_incidents_flow():
    # Trigger simulation
    response = client.post("/simulate-alert")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "simulation_completed"
    assert "incident_id" in data
    assert data["root_cause"] != ""
    assert data["rollback_command"] != ""

    incident_id = data["incident_id"]

    # Verify incident is in /incidents list
    list_resp = client.get("/incidents")
    assert list_resp.status_code == 200
    incidents = list_resp.json()
    assert any(inc["incident_id"] == incident_id for inc in incidents)

    # Verify /incidents/{incident_id}
    detail_resp = client.get(f"/incidents/{incident_id}")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert detail["incident_id"] == incident_id
    assert detail["alertname"] == "HighSubscriptionCreationFailureRate"

    # Verify /incidents/{incident_id}/report returns Markdown
    report_resp = client.get(f"/incidents/{incident_id}/report")
    assert report_resp.status_code == 200
    assert report_resp.headers["content-type"].startswith("text/plain")
    assert "# 🚨 Incident Report" in report_resp.text


def test_api_alerts_webhook_firing():
    payload = {
        "receiver": "subtracker-oncall-webhook",
        "status": "firing",
        "alerts": [
            {
                "status": "firing",
                "labels": {
                    "alertname": "HighSubscriptionCreationFailureRate",
                    "service": "subtracker-backend",
                    "environment": "dev",
                    "deployed_version": "20261116-test-tag",
                    "severity": "critical",
                },
                "annotations": {
                    "summary": "Webhook test alert",
                    "description": "Simulated rate failure",
                },
            }
        ],
    }

    response = client.post("/alerts", json=payload)
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["status"] == "success"
    assert res_data["processed_count"] == 1
    assert len(res_data["incidents"]) == 1
    assert res_data["incidents"][0]["alertname"] == "HighSubscriptionCreationFailureRate"
