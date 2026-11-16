# SubTracker AI On-Call Responder Agent

The **SubTracker AI On-Call Responder Agent** is an autonomous incident response service for the SubTracker platform. It listens for firing Grafana alerting webhooks on port `8080` at `POST /alerts`, automatically aggregates deep diagnostic context from across the observability stack, performs Root-Cause Analysis (RCA) via LLMs, and publishes actionable remediation reports with rollback commands and code patches.

---

## 🏛️ Architecture & Incident Workflow

```
 ┌────────────────────────────────────────────────────────┐
 │            Grafana Alert Rule Evaluator                │
 │  (e.g., HighSubscriptionCreationFailureRate firing)    │
 └───────────────────────────┬────────────────────────────┘
                             │ POST /alerts (JSON webhook)
                             ▼
 ┌────────────────────────────────────────────────────────┐
 │           AI On-Call Responder Agent (Port 8080)       │
 └───────┬───────────────────┬────────────────────┬───────┘
         │                   │                    │
         │ 1. Loki API       │ 2. Tempo API       │ 3. Prometheus API
         ▼                   ▼                    ▼
   Recent ERROR Logs   Trace Spans & 5xx    Failure Rate & Active
   & Stacktraces       HTTP Requests        Subscription Metrics
         │                   │                    │
         └───────────────────┼────────────────────┘
                             │
                             ▼
         4. Correlate with Recent Git Commits & Tags
                             │
                             ▼
         5. LLM Root-Cause Analysis (RCA) Engine
            (OpenAI / Anthropic / Gemini / Heuristics)
            - Technical root cause diagnosis
            - Immediate mitigation steps
            - Exact rollback command
            - Concrete code patch / unified diff
                             │
                             ▼
         6. Automated Incident Publication
            ├── Markdown Incident Report in /app/incidents
            └── GitHub Issue with labels ['incident', 'oncall-rca']
```

---

## ⚙️ Configuration & Environment Variables

The responder agent is configured via environment variables in `observability/docker-compose.yml` or a local `.env`:

| Variable | Default | Description |
| :--- | :--- | :--- |
| `PORT` | `8080` | Port on which the FastAPI application listens |
| `LOKI_URL` | `http://loki:3100` | Loki query endpoint (`/loki/api/v1/query_range`) |
| `TEMPO_URL` | `http://tempo:3200` | Tempo search endpoint (`/api/search`) |
| `PROMETHEUS_URL` | `http://prometheus:9090` | Prometheus query endpoint (`/api/v1/query`) |
| `INCIDENTS_DIR` | `/app/incidents` | Path where local Markdown incident reports are saved |
| `OPENAI_API_KEY` | `""` | Optional: OpenAI API Key for GPT-4o analysis |
| `ANTHROPIC_API_KEY`| `""` | Optional: Anthropic API Key for Claude 3.5 Sonnet analysis |
| `GEMINI_API_KEY` | `""` | Optional: Google Gemini API Key for Gemini 1.5 analysis |
| `GITHUB_TOKEN` | `""` | Optional: GitHub personal access token to create incident issues |
| `GITHUB_REPOSITORY`| `Solikh228/LinkHealth` | GitHub repository for opening automated incident issues |

> [!NOTE]
> If no LLM API keys (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`) are set, the agent automatically falls back to an **autonomous deterministic heuristics engine**. This guarantees the on-call agent works fully offline, during local development, and in automated CI test environments without external dependencies.

---

## 🚀 Running the Agent

### Inside Docker Compose (Observability Stack)
The on-call agent is included as a service in `observability/docker-compose.yml`:
```bash
cd observability
docker compose up -d oncall-agent
```

### Running Locally with uv
```bash
cd observability/oncall-agent
uv run uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

---

## 📡 API Endpoints

### 1. `POST /alerts`
Webhook receiver matching Grafana's Contact Point configuration. Parses alert labels, annotations, queries observability telemetry, runs the RCA engine, and publishes incident reports.

**Request**: Standard Grafana Alertmanager webhook JSON payload.

### 2. `POST /simulate-alert`
Triggers an immediate end-to-end incident investigation simulation of a firing `HighSubscriptionCreationFailureRate` alert without needing to wait for live metrics.

```bash
curl -X POST http://localhost:8080/simulate-alert
```

**Response Example**:
```json
{
  "status": "simulation_completed",
  "incident_id": "inc_20261116_140000_a1b2c3",
  "summary": "High subscription creation failure rate (4.5/min) sustained for > 2m on subtracker-backend (dev).",
  "root_cause": "Pydantic request/response schema validation mismatch on subscription creation payload.",
  "rollback_command": "docker compose -f docker-compose.prod.yml down && sed -i 's|^APP_IMAGE=.*|APP_IMAGE=subtracker:latest|' .env && docker compose -f docker-compose.prod.yml up -d",
  "incident_file": "/app/incidents/inc_20261116_140000_a1b2c3_HighSubscriptionCreationFailureRate.md",
  "github_issue": null
}
```

### 3. `GET /incidents`
Lists all recently analyzed incidents.

### 4. `GET /incidents/{incident_id}`
Returns structured JSON data for a specific incident.

### 5. `GET /incidents/{incident_id}/report`
Returns the raw, formatted Markdown incident report ready for human review or Slack/email distribution.

### 6. `GET /health`
Healthcheck endpoint returning `{ "status": "ok", "service": "subtracker-oncall-agent" }`.

---

## 🧪 Testing

To run the unit test suite verifying webhook parsing, telemetry aggregation, LLM/heuristic RCA, and FastAPI endpoints:

```bash
uv run --directory backend pytest ../observability/oncall-agent/tests/test_oncall_agent.py -v
```
