# System Architect & Technical Governance

## Role Description
You are the System Architect for SubTracker. You define the technical architecture, domain models, entity relationships, and systemic constraints.

## Architecture Principles

### 1. Strict Client-Server Decoupling
- The system is divided cleanly into `frontend/` and `backend/`.
- Frontend communicates with backend exclusively via HTTP REST over JSON adhering to the OpenAPI 3.0 specification (`contract/openapi.yaml`).
- Zero direct database access from frontend code.

### 2. Zero External SaaS / Local Execution
- Zero external cloud database dependencies (no Supabase, DynamoDB, or external cloud DB required for operation).
- Local storage default using SQLite (`subtracker.db` / `app.db`) managed through SQLAlchemy ORM.
- Database-agnostic design: configurable via `DATABASE_URL` environment variable for future PostgreSQL / MySQL deployments.
- Synthetic ingestion harnesses provide realistic bank transactions and email evidence locally without live third-party API dependencies.

## Entity Relationship Diagram (ERD)

```mermaid
erDiagram
    User ||--o{ Workspace : owns
    User ||--o{ UserReview : authors
    Workspace ||--o{ IntegrationConnection : configures
    IntegrationConnection ||--o{ Transaction : imports
    Subscription ||--o{ Transaction : matches
    Subscription ||--o{ EmailEvidence : matches
    Subscription ||--o{ Finding : generates
    Finding ||--o{ UserReview : reviewed_by

    User {
        string id PK
        string email UK
        string password_hash
        string created_at
    }

    Workspace {
        string id PK
        string name
        string owner_user_id FK
        string base_currency
        string created_at
    }

    IntegrationConnection {
        string id PK
        string kind
        string provider
        string display_name
        string status
        string sync_state
        json scopes_granted
        string last_sync_at
        string last_sync_status
        string created_at
    }

    Subscription {
        string id PK
        string vendor_name
        string vendor_domain
        string category
        string display_name
        string status
        string billing_interval
        int expected_amount_minor
        string expected_amount_currency
        int monthly_equivalent_minor
        string monthly_equivalent_currency
        string estimated_next_charge_at
        float detection_confidence
        string detection_explanation
        string last_detected_at
        string note
    }

    Transaction {
        string id PK
        string connection_id FK
        string account_name
        string posted_at
        int amount_minor
        string amount_currency
        string description_raw
        string merchant_normalized
        string status
        boolean is_recurring_candidate
        string subscription_id FK
    }

    EmailEvidence {
        string id PK
        string subscription_id FK
        string received_at
        string sender_domain
        string subject_minimized
        string evidence_type
        int amount_minor
        string amount_currency
        string invoice_date
        float extraction_confidence
        float match_score
        string match_status
        string match_reason
    }

    Finding {
        string id PK
        string subscription_id FK
        string subscription_name
        string finding_type
        string severity
        string status
        string title
        string explanation
        int estimated_impact_minor
        string estimated_impact_currency
        float confidence
        string rule_version
        string created_at
        string updated_at
    }

    UserReview {
        string id PK
        string finding_id FK
        string decision
        string note
        int estimated_savings_minor
        string estimated_savings_currency
        string created_at
    }
```

## Issue Labeling Governance
- `mvp`: Mandatory architectural features for initial autonomous release.
- `post-mvp`: Scale enhancements, external OAuth providers, and automated bank webhook workers.
- `user-test-bug`: Defect remediation during QA pilot testing.
