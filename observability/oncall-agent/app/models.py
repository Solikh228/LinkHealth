"""
Data models for Grafana alert webhooks, telemetry context, and incident RCA reports.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class GrafanaAlertItem(BaseModel):
    status: str = Field("firing", description="Alert status (firing, resolved)")
    labels: Dict[str, str] = Field(default_factory=dict)
    annotations: Dict[str, str] = Field(default_factory=dict)
    startsAt: Optional[str] = None
    endsAt: Optional[str] = None
    generatorURL: Optional[str] = None
    fingerprint: Optional[str] = None


class GrafanaAlertPayload(BaseModel):
    receiver: Optional[str] = "subtracker-oncall-webhook"
    status: str = "firing"
    alerts: List[GrafanaAlertItem] = Field(default_factory=list)
    groupLabels: Dict[str, str] = Field(default_factory=dict)
    commonLabels: Dict[str, str] = Field(default_factory=dict)
    commonAnnotations: Dict[str, str] = Field(default_factory=dict)
    externalURL: Optional[str] = ""
    version: Optional[str] = "1"


class TelemetryContext(BaseModel):
    alertname: str
    service: str
    environment: str
    deployed_version: str
    failure_metric_rate: float = 0.0
    active_subscriptions: Optional[int] = None
    active_users: Optional[int] = None
    loki_logs: List[str] = Field(default_factory=list)
    tempo_traces: List[Dict[str, Any]] = Field(default_factory=list)
    git_commits: List[Dict[str, str]] = Field(default_factory=list)
    query_timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class RCAReport(BaseModel):
    incident_id: str
    alertname: str
    status: str = "firing"
    service: str
    environment: str
    deployed_version: str
    severity: str = "critical"
    summary: str
    root_cause: str
    evidence_logs: List[str] = Field(default_factory=list)
    evidence_traces: List[Dict[str, Any]] = Field(default_factory=list)
    current_metrics: Dict[str, Any] = Field(default_factory=dict)
    immediate_mitigation: str
    rollback_command: str
    code_patch: Optional[str] = None
    preventative_actions: List[str] = Field(default_factory=list)
    dashboard_url: Optional[str] = None
    runbook_url: Optional[str] = None
    github_issue_url: Optional[str] = None
    incident_file_path: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
