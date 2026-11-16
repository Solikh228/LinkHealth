"""
FastAPI On-Call Responder Agent for Grafana Alerts.
Listens on port 8080, analyzes firing alerts with telemetry context, and generates
automated RCA reports with proposed fixes and rollback commands.
"""

import logging
import os
from typing import Any, Dict, List
from fastapi import BackgroundTasks, FastAPI, HTTPException, status
from fastapi.responses import JSONResponse, PlainTextResponse

from .llm_engine import LLMEngine
from .models import GrafanaAlertItem, GrafanaAlertPayload, RCAReport
from .publisher import IncidentPublisher
from .telemetry_client import TelemetryClient

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("oncall-agent")

app = FastAPI(
    title="SubTracker AI On-Call Responder Agent",
    description="Automated incident investigation, root-cause analysis (RCA), and remediation for Grafana alerts",
    version="1.0.0",
)

telemetry_client = TelemetryClient()
llm_engine = LLMEngine()
publisher = IncidentPublisher()

# In-memory store of recent analyzed incidents
recent_incidents: Dict[str, RCAReport] = {}


async def process_alert(alert: GrafanaAlertItem) -> RCAReport:
    """End-to-end alert investigation and publication pipeline."""
    labels = alert.labels
    alertname = labels.get("alertname", "UnknownAlert")
    service = labels.get("service", "subtracker-backend")
    environment = labels.get("environment", "dev")

    logger.info(f"Processing alert: '{alertname}' on service '{service}' ({environment}, status: {alert.status})")

    # 1. Aggregate telemetry context from Loki, Tempo, Prometheus, Git
    context = await telemetry_client.aggregate_context(alert)

    # 2. Analyze root-cause using LLM or heuristic engine
    rca = await llm_engine.analyze_incident(alert, context)

    # 3. Publish incident report locally and create GitHub Issue
    published_rca = await publisher.publish(rca)

    # 4. Save to in-memory history
    recent_incidents[published_rca.incident_id] = published_rca
    logger.info(f"Successfully generated incident report: {published_rca.incident_id}")

    return published_rca


@app.post("/alerts", status_code=status.HTTP_200_OK)
async def receive_grafana_alerts(payload: GrafanaAlertPayload, background_tasks: BackgroundTasks):
    """
    Grafana Contact Point Webhook receiver endpoint.
    Receives JSON alert notifications, investigates firing alerts, and produces RCAs.
    """
    logger.info(f"Received Grafana webhook: status={payload.status}, alerts_count={len(payload.alerts)}")

    processed_reports = []
    firing_alerts = [a for a in payload.alerts if a.status.lower() == "firing"]

    if not firing_alerts and payload.status.lower() == "firing":
        # Fallback if alerts list is empty but top-level status is firing
        firing_alerts = [
            GrafanaAlertItem(
                status="firing",
                labels=payload.commonLabels or payload.groupLabels,
                annotations=payload.commonAnnotations,
            )
        ]

    for alert in firing_alerts:
        rca = await process_alert(alert)
        processed_reports.append({
            "incident_id": rca.incident_id,
            "alertname": rca.alertname,
            "summary": rca.summary,
            "root_cause": rca.root_cause,
            "file": rca.incident_file_path,
            "github_issue": rca.github_issue_url,
        })

    return {
        "status": "success",
        "receiver": payload.receiver,
        "processed_count": len(processed_reports),
        "incidents": processed_reports,
    }


@app.post("/simulate-alert", status_code=status.HTTP_200_OK)
async def simulate_alert():
    """
    Simulate a firing 'HighSubscriptionCreationFailureRate' alert to test
    the end-to-end investigation, RCA generation, and publishing pipeline.
    """
    simulated_payload = GrafanaAlertPayload(
        receiver="subtracker-oncall-webhook",
        status="firing",
        commonLabels={
            "alertname": "HighSubscriptionCreationFailureRate",
            "service": "subtracker-backend",
            "environment": "dev",
            "deployed_version": "20261116-140000-sha123",
            "severity": "critical",
            "owner": "subtracker-oncall",
        },
        commonAnnotations={
            "summary": "High subscription creation failure rate on subtracker-backend (dev)",
            "description": "Subscription creation failure rate is 4.5 failures/min exceeding 3.0 threshold for > 2m.",
            "dashboard_url": "http://localhost:3000/d/subtracker-otel-overview/subtracker-opentelemetry-observability",
            "runbook_url": "https://github.com/Solikh228/LinkHealth/blob/main/docs/runbooks/subscription-creation-failures.md",
        },
        alerts=[
            GrafanaAlertItem(
                status="firing",
                labels={
                    "alertname": "HighSubscriptionCreationFailureRate",
                    "service": "subtracker-backend",
                    "environment": "dev",
                    "deployed_version": "20261116-140000-sha123",
                    "severity": "critical",
                    "owner": "subtracker-oncall",
                },
                annotations={
                    "summary": "High subscription creation failure rate on subtracker-backend (dev)",
                    "description": "Subscription creation failure rate is 4.5 failures/min exceeding 3.0 threshold for > 2m.",
                    "dashboard_url": "http://localhost:3000/d/subtracker-otel-overview/subtracker-opentelemetry-observability",
                    "runbook_url": "https://github.com/Solikh228/LinkHealth/blob/main/docs/runbooks/subscription-creation-failures.md",
                },
            )
        ],
    )

    alert = simulated_payload.alerts[0]
    rca = await process_alert(alert)

    return {
        "status": "simulation_completed",
        "incident_id": rca.incident_id,
        "summary": rca.summary,
        "root_cause": rca.root_cause,
        "rollback_command": rca.rollback_command,
        "incident_file": rca.incident_file_path,
        "github_issue": rca.github_issue_url,
    }


@app.get("/incidents", response_model=List[Dict[str, Any]])
def list_incidents():
    """List all analyzed incidents in memory."""
    return [
        {
            "incident_id": r.incident_id,
            "alertname": r.alertname,
            "service": r.service,
            "environment": r.environment,
            "severity": r.severity,
            "summary": r.summary,
            "created_at": r.created_at,
            "file": r.incident_file_path,
            "github_issue": r.github_issue_url,
        }
        for r in recent_incidents.values()
    ]


@app.get("/incidents/{incident_id}")
def get_incident(incident_id: str):
    """Retrieve full details of an analyzed incident."""
    if incident_id not in recent_incidents:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident '{incident_id}' not found",
        )
    return recent_incidents[incident_id]


@app.get("/incidents/{incident_id}/report", response_class=PlainTextResponse)
def get_incident_report(incident_id: str):
    """Retrieve raw Markdown incident report."""
    if incident_id not in recent_incidents:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident '{incident_id}' not found",
        )
    return publisher.format_markdown(recent_incidents[incident_id])


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "subtracker-oncall-agent",
        "incidents_analyzed": len(recent_incidents),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8080, reload=True)
