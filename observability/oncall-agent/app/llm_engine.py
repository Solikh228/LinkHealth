"""
LLM Root-Cause Analysis (RCA) Engine.
Integrates with OpenAI, Anthropic, or Gemini APIs, with a robust heuristic fallback
engine for offline testing and autonomous self-healing.
"""

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional
import httpx

from .models import GrafanaAlertItem, RCAReport, TelemetryContext

logger = logging.getLogger("oncall-agent.llm")


class LLMEngine:
    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
        gemini_api_key: Optional[str] = None,
    ):
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.anthropic_api_key = anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
        self.gemini_api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")

    def _build_prompt(self, alert: GrafanaAlertItem, context: TelemetryContext) -> str:
        """Construct the diagnostic prompt with all aggregated telemetry."""
        labels = alert.labels
        annotations = alert.annotations

        commits_str = "\n".join(
            [f"- [{c.get('sha')}] {c.get('message')} (by {c.get('author')})" for c in context.git_commits]
        )
        logs_str = "\n".join(context.loki_logs) if context.loki_logs else "No explicit stacktrace found in Loki."
        traces_str = json.dumps(context.tempo_traces, indent=2) if context.tempo_traces else "No traces captured."

        prompt = f"""You are the SubTracker AI On-Call Incident Responder.
A critical alert has fired in Grafana. Analyze the provided telemetry and generate a complete Root-Cause Analysis (RCA) with an actionable remediation.

ALERT DETAILS:
- Alert Name: {labels.get('alertname', 'HighSubscriptionCreationFailureRate')}
- Service: {context.service}
- Environment: {context.environment}
- Deployed Version / Tag: {context.deployed_version}
- Severity: {labels.get('severity', 'critical')}
- Summary: {annotations.get('summary', '')}
- Description: {annotations.get('description', '')}

OBSERVABILITY METRICS:
- Failure Rate: {context.failure_metric_rate:.2f} failures/min (Threshold: 3.0/min)
- Active Subscriptions: {context.active_subscriptions}
- Active Users: {context.active_users}

RECENT LOKI ERROR LOGS:
{logs_str}

RECENT TEMPO TRACES:
{traces_str}

RECENT GIT COMMITS:
{commits_str}

Please analyze the root cause and reply ONLY with a valid JSON object matching this schema:
{{
  "summary": "Concise 1-2 sentence incident summary",
  "root_cause": "Detailed technical explanation of what failed and why",
  "immediate_mitigation": "Immediate step to mitigate user impact",
  "rollback_command": "Exact command to rollback container image or git commit",
  "code_patch": "Unified git diff or code fix snippet (optional)",
  "preventative_actions": ["Action item 1", "Action item 2"]
}}
"""
        return prompt

    async def _call_openai(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Call OpenAI API."""
        try:
            model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.openai_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model,
                        "messages": [
                            {"role": "system", "content": "You are an automated on-call incident responder. Output valid JSON."},
                            {"role": "user", "content": prompt},
                        ],
                        "response_format": {"type": "json_object"},
                        "temperature": 0.2,
                    },
                )
                if resp.status_code == 200:
                    data = resp.json()
                    content = data["choices"][0]["message"]["content"]
                    return json.loads(content)
        except Exception as e:
            logger.warning(f"OpenAI API call failed: {e}")
        return None

    async def _call_anthropic(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Call Anthropic API."""
        try:
            model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": self.anthropic_api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={
                        "model": model,
                        "max_tokens": 1500,
                        "messages": [{"role": "user", "content": prompt}],
                    },
                )
                if resp.status_code == 200:
                    data = resp.json()
                    content = data["content"][0]["text"]
                    # Extract JSON block
                    start = content.find("{")
                    end = content.rfind("}") + 1
                    if start != -1 and end != -1:
                        return json.loads(content[start:end])
        except Exception as e:
            logger.warning(f"Anthropic API call failed: {e}")
        return None

    async def _call_gemini(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Call Google Gemini API."""
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini_api_key}"
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    url,
                    json={
                        "contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": {"responseMimeType": "application/json"},
                    },
                )
                if resp.status_code == 200:
                    data = resp.json()
                    text = data["candidates"][0]["content"]["parts"][0]["text"]
                    return json.loads(text)
        except Exception as e:
            logger.warning(f"Gemini API call failed: {e}")
        return None

    def _heuristic_rca(self, alert: GrafanaAlertItem, context: TelemetryContext) -> Dict[str, Any]:
        """
        Deterministic, rule-based RCA engine used when API keys are not supplied.
        Analyzes logs, traces, and metrics to provide concrete root cause diagnosis.
        """
        recent_commit = context.git_commits[0].get("sha", "HEAD") if context.git_commits else "HEAD"
        rate = context.failure_metric_rate or 4.5

        # Inspect logs for signatures
        logs_joined = " ".join(context.loki_logs).lower()
        if "validation" in logs_joined or "field required" in logs_joined:
            reason = "Pydantic request/response schema validation mismatch on subscription creation payload."
            patch = (
                "--- a/backend/routers/subscriptions.py\n"
                "+++ b/backend/routers/subscriptions.py\n"
                "@@ -70,6 +70,7 @@ def create_subscription(payload: SubscriptionCreateRequest):\n"
                "+        lastChargeDate=payload.lastChargeDate or datetime.now(timezone.utc).strftime('%Y-%m-%d'),\n"
            )
        elif "connection" in logs_joined or "pool" in logs_joined:
            reason = "PostgreSQL connection pool exhaustion under elevated request volume."
            patch = (
                "# Increase pool size in backend/.env:\n"
                "DB_POOL_SIZE=25\n"
                "DB_MAX_OVERFLOW=50\n"
            )
        else:
            reason = f"Elevated subscription creation failure rate ({rate:.1f}/min exceeding 3.0/min threshold). Handlers encountering validation errors or unhandled exceptions."
            patch = (
                "--- a/backend/routers/subscriptions.py\n"
                "+++ b/backend/routers/subscriptions.py\n"
                "@@ -65,3 +65,5 @@\n"
                "+    # Ensure all required fields have robust default values\n"
                "+    sub_obj.lastChargeDate = sub_obj.lastChargeDate or datetime.now(timezone.utc).strftime('%Y-%m-%d')\n"
            )

        return {
            "summary": f"High subscription creation failure rate ({rate:.1f}/min) sustained for > 2m on {context.service} ({context.environment}).",
            "root_cause": reason,
            "immediate_mitigation": "Restart subtracker container or rollback to previous stable deployment tag.",
            "rollback_command": f"docker compose -f docker-compose.prod.yml down && sed -i 's|^APP_IMAGE=.*|APP_IMAGE=subtracker:latest|' .env && docker compose -f docker-compose.prod.yml up -d",
            "code_patch": patch,
            "preventative_actions": [
                "Add integration test verifying all subscription creation schema invariants",
                "Ensure frontend sends explicit ISO-8601 lastChargeDate with fallback defaults",
                "Tune database connection pool limits and timeouts in production .env",
            ],
        }

    async def analyze_incident(self, alert: GrafanaAlertItem, context: TelemetryContext) -> RCAReport:
        """Run RCA analysis using available LLM API or heuristic engine."""
        incident_id = f"inc_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        prompt = self._build_prompt(alert, context)

        llm_response = None
        if self.openai_api_key:
            logger.info("Performing incident RCA via OpenAI API...")
            llm_response = await self._call_openai(prompt)
        elif self.anthropic_api_key:
            logger.info("Performing incident RCA via Anthropic API...")
            llm_response = await self._call_anthropic(prompt)
        elif self.gemini_api_key:
            logger.info("Performing incident RCA via Gemini API...")
            llm_response = await self._call_gemini(prompt)

        if not llm_response:
            logger.info("Using automated heuristic on-call RCA engine...")
            llm_response = self._heuristic_rca(alert, context)

        annotations = alert.annotations
        labels = alert.labels

        return RCAReport(
            incident_id=incident_id,
            alertname=labels.get("alertname", "HighSubscriptionCreationFailureRate"),
            status=alert.status,
            service=context.service,
            environment=context.environment,
            deployed_version=context.deployed_version,
            severity=labels.get("severity", "critical"),
            summary=llm_response.get("summary", "Repeated subscription creation failures detected"),
            root_cause=llm_response.get("root_cause", "Unspecified error rate spike"),
            evidence_logs=context.loki_logs[:10],
            evidence_traces=context.tempo_traces[:5],
            current_metrics={
                "failure_rate_per_min": context.failure_metric_rate,
                "active_subscriptions": context.active_subscriptions,
                "active_users": context.active_users,
            },
            immediate_mitigation=llm_response.get("immediate_mitigation", "Inspect service logs and restart"),
            rollback_command=llm_response.get("rollback_command", "docker compose up -d"),
            code_patch=llm_response.get("code_patch"),
            preventative_actions=llm_response.get("preventative_actions", []),
            dashboard_url=annotations.get("dashboard_url"),
            runbook_url=annotations.get("runbook_url"),
        )
