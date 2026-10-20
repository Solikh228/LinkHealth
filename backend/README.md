# SubTracker FastAPI Backend

FastAPI implementation for **SubTracker** (Hidden B2B Subscriptions & Auto-Charge Tracker), implementing the OpenAPI specification with in-memory persistence and JWT bearer authentication.

## Modules Structure
```text
backend/
├── app/
│   ├── main.py              # FastAPI app entrypoint, CORS, and router registration
│   ├── models/              # Domain DTOs and Pydantic v2 schemas
│   │   ├── auth.py          # User, Workspace, Session models
│   │   ├── common.py        # Money, Paginated models
│   │   ├── dashboard.py     # DashboardSummary, Upcoming, Category breakdown
│   │   ├── findings.py      # Finding, FindingDetail, ReviewInput, UserReview
│   │   ├── integrations.py  # IntegrationConnection, Connect, Disconnect
│   │   ├── subscriptions.py # Subscription, SubscriptionDetail, Patch, Evidence
│   │   └── transactions.py  # Transaction, TransactionQuery
│   ├── auth/                # Security and authentication
│   │   ├── security.py      # Bcrypt password hashing, JWT creation & verification
│   │   └── dependencies.py  # get_current_user and get_optional_user guards
│   ├── store/               # In-memory storage and seed fixtures
│   │   ├── memory.py        # Thread-safe InMemoryStore
│   │   └── seeds.py         # Realistic seed data matching mock.ts & plan.md
│   └── routers/             # Endpoint routers
│       ├── auth.py          # /auth/session, /me, /workspace, /account
│       ├── dashboard.py     # /dashboard/summary
│       ├── findings.py      # /findings, /findings/{id}, /findings/{id}/review
│       ├── integrations.py  # /integrations, connect, sync, disconnect
│       ├── subscriptions.py # /subscriptions, get, patch, confirm, dismiss
│       └── transactions.py  # /transactions with pagination and search
├── tests/                   # Automated test suite (25 tests)
├── scripts/                 # Utility scripts (OpenAPI export)
├── pyproject.toml           # uv project configuration and dependencies
└── openapi.yaml             # Exported OpenAPI 3.1 specification
```

## Setup & Running

Managed with `uv`:

```bash
# Sync dependencies
uv sync

# Run development server
uv run uvicorn app.main:app --reload --port 8000

# Run automated tests
uv run pytest

# Export updated OpenAPI specification
uv run python scripts/export_openapi.py
```

## Default Credentials
- **Email:** `alex@studio.dev`
- **Password:** `password123`
*(Any new email will automatically provision a new user on first login).*
