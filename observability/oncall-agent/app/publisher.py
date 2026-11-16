"""
Incident Report Publisher.
Saves structured Markdown incident documents locally and creates GitHub Issues.
"""

import json
import logging
import os
from pathlib import Path
from typing import Optional
import httpx

from .models import RCAReport

logger = logging.getLogger("oncall-agent.publisher")


class IncidentPublisher:
    def __init__(
        self,
        incidents_dir: Optional[str] = None,
        github_token: Optional[str] = None,
        github_repository: Optional[str] = None,
    ):
        default_dir = Path(__file__).resolve().parent.parent / "incidents"
        self.incidents_dir = Path(
            incidents_dir or os.getenv("INCIDENTS_DIR") or default_dir
        )
        self.incidents_dir.mkdir(parents=True, exist_ok=True)
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        self.github_repository = github_repository or os.getenv("GITHUB_REPOSITORY", "Solikh228/LinkHealth")

    def format_markdown(self, rca: RCAReport) -> str:
        """Render a formatted, actionable Markdown Incident Report."""
        preventative = "\n".join([f"- {item}" for item in rca.preventative_actions]) or "- Review integration tests"
        logs_block = "\n".join(rca.evidence_logs) if rca.evidence_logs else "No explicit stacktrace captured."
        traces_block = json.dumps(rca.evidence_traces, indent=2) if rca.evidence_traces else "[]"
        metrics_block = json.dumps(rca.current_metrics, indent=2)

        patch_section = ""
        if rca.code_patch:
            patch_section = f"""
### 🛠️ Proposed Code Patch
```diff
{rca.code_patch}
```
"""

        doc = f"""# 🚨 Incident Report: {rca.alertname}

**Incident ID**: `{rca.incident_id}`  
**Status**: `{rca.status.upper()}`  
**Severity**: `{rca.severity.upper()}`  
**Service**: `{rca.service}`  
**Environment**: `{rca.environment}`  
**Deployed Version**: `{rca.deployed_version}`  
**Timestamp**: `{rca.created_at}`  

---

## 📋 Executive Summary
{rca.summary}

---

## 🔍 Root Cause Analysis (RCA)
{rca.root_cause}

---

## ⚡ Immediate Mitigation & Rollback
**Action**: {rca.immediate_mitigation}

```bash
# Execute immediate rollback on {rca.environment}:
{rca.rollback_command}
```
{patch_section}
---

## 📊 Telemetry Diagnostics

### Current Metric Rates
```json
{metrics_block}
```

### Loki Log Evidence
```text
{logs_block}
```

### Tempo Traces Context
```json
{traces_block}
```

---

## 🛡️ Preventative Actions
{preventative}

---

## 🔗 Useful Links
- **Grafana Dashboard**: [{rca.service} Overview]({rca.dashboard_url or '#'})
- **Runbook**: [{rca.alertname} Runbook]({rca.runbook_url or '#'})
"""
        return doc

    def save_local_report(self, rca: RCAReport) -> str:
        """Save incident report as a local Markdown document."""
        filename = f"{rca.incident_id}_{rca.alertname}.md"
        filepath = self.incidents_dir / filename
        content = self.format_markdown(rca)
        filepath.write_text(content, encoding="utf-8")
        logger.info(f"Saved local incident report to: {filepath}")
        return str(filepath)

    async def create_github_issue(self, rca: RCAReport) -> Optional[str]:
        """Create a GitHub Issue if GITHUB_TOKEN is available."""
        if not self.github_token:
            logger.info("GITHUB_TOKEN not configured. Skipping GitHub Issue creation.")
            return None

        url = f"https://api.github.com/repos/{self.github_repository}/issues"
        title = f"[INCIDENT] {rca.alertname} on {rca.service} ({rca.environment})"
        body = self.format_markdown(rca)

        headers = {
            "Authorization": f"Bearer {self.github_token}",
            "Accept": "application/vnd.github.v3+json",
        }
        payload = {
            "title": title,
            "body": body,
            "labels": ["incident", "oncall-rca", "automated", rca.severity],
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code == 201:
                    issue_data = resp.json()
                    issue_url = issue_data.get("html_url")
                    logger.info(f"Created GitHub Issue: {issue_url}")
                    return issue_url
                else:
                    logger.warning(f"Failed to create GitHub Issue: {resp.status_code} {resp.text}")
        except Exception as e:
            logger.warning(f"Error creating GitHub Issue: {e}")

        return None

    async def publish(self, rca: RCAReport) -> RCAReport:
        """Publish incident report locally and to GitHub if configured."""
        filepath = self.save_local_report(rca)
        rca.incident_file_path = filepath

        github_url = await self.create_github_issue(rca)
        if github_url:
            rca.github_issue_url = github_url

        return rca
