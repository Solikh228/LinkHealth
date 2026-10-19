# SubTracker (Hidden B2B Subscriptions & Waste Finder Tracker) - Backlog

This backlog defines the implementation roadmap for the B2B Hidden Subscriptions & Waste Tracker, aligned with `_docs/plan.md` and strictly governed by the local-first, zero-cloud architectural constraints.

---

# Phase 1: Frontend with Mock Service

## 1. Project Scaffolding and Smoke Test Setup
Tag: `mvp`

### Goal
Establish the root repository structure with separated client, backend, contract, and documentation workspaces, along with an automated test runner executing a passing smoke test.

### Acceptance criteria
- [ ] Running `python -m pytest` from repository root discovers `tests/test_smoke.py` and passes with 0 failures
- [ ] Top-level directories `frontend/`, `backend/`, `contract/`, and `_docs/` exist
- [ ] File `tests/test_smoke.py` exists and asserts environment sanity
- [ ] Root `README.md` documents dependencies, local setup, and testing commands
- [ ] Zero external cloud database or external SaaS credentials are required to run tests

### Out of scope
- Full frontend UI implementation, moved to #3
- Backend server scaffolding, moved to #11

### Constraints
- Stay inside root files (`README.md`, `pyproject.toml`, `tests/test_smoke.py`)
- Python 3.14 with pytest
- Strict client-server directory decoupling

---

## 2. Repository Governance and Role Workflow Documentation
Tag: `mvp`

### Goal
Author the repository root governance documents defining team roles, architectural constraints, test criteria, and issue lifecycle protocols.

### Acceptance criteria
- [ ] `pm.md` exists at repository root defining issue grooming and the 4-section task template
- [ ] `architect.md` exists at repository root specifying the entity relationship diagram (ERD), decoupled REST architecture, local SQLite database rule, and zero-external-SaaS constraints
- [ ] `qa-engineer.md` exists at repository root defining verification checklists, the verdict format (PASS/FAIL), and the mandatory bug template (`Goal`, `Reproduction Steps`, `Observed Behavior`, `Expected Behavior`)
- [ ] `brainstorm_chat_history.md` exists at repository root logging the TrustMRR / B2B waste finder rationale, customer positioning, and scope trade-offs from `_docs/plan.md`
- [ ] GitHub issue labeling strategy (`mvp`, `post-mvp`, `user-test-bug`) is clearly documented across governance files

### Out of scope
- Application feature code or mock datasets, moved to #3 and #4

### Constraints
- Stay inside root markdown files (`pm.md`, `architect.md`, `qa-engineer.md`, `brainstorm_chat_history.md`)
- Adhere strictly to the AI Shipping Framework role definitions

---

## 3. Frontend Scaffolding with Tailwind CSS and Component Library
Tag: `mvp`

### Goal
Scaffold the client-side single page application in `frontend/` using Vite, React, TypeScript, Tailwind CSS, Lucide icons, and core shadcn/ui components.

### Acceptance criteria
- [ ] Running `npm run dev` in `frontend/` serves the development server on `http://localhost:5173` without warnings
- [ ] Running `npm run build` compiles the React TypeScript app with zero errors
- [ ] Application shell renders top navigation bar with SubTracker branding, navigation links (Overview, Subscriptions, Waste Finder, Renewals, Connections), and user avatar
- [ ] Base shadcn/ui primitives (`Button`, `Card`, `Badge`, `Input`, `Dialog`, `Table`, `Tabs`) are installed and functional
- [ ] Tailwind typography and color palettes render consistently across desktop and mobile viewports

### Out of scope
- Mock service and fixture implementation, moved to #4
- Dashboard page views, moved to #5, #6, #7, #8, #9

### Constraints
- Stay inside `frontend/`
- Vite + React 18/19 + TypeScript + Tailwind CSS
- Pure SPA architecture (no server actions or Next.js SSR)

---

## 4. Frontend Mock Service and Synthetic Subscription Fixtures
Tag: `mvp`

### Goal
Implement an isolated mock service and realistic synthetic fixture dataset reflecting bank transactions and Gmail billing evidence so that the UI runs completely offline.

### Acceptance criteria
- [ ] `frontend/src/services/mockService.ts` exports typed methods: `getOverviewMetrics`, `getSubscriptions`, `getSubscriptionById`, `getFindings`, `updateFindingDecision`, `getRenewals`, `getConnections`, `triggerSync`, `disconnectConnection`, and `deleteUserData`
- [ ] TypeScript interfaces for `Subscription`, `Finding`, `Transaction`, `BillingEvidence`, `Connection`, and `OverviewMetrics` are defined in `frontend/src/types/index.ts` strictly mirroring `_docs/plan.md`
- [ ] Synthetic fixtures include at least 8 realistic business subscriptions (e.g. AWS, GitHub, Figma, Google Workspace, Zoom, Adobe Creative Cloud, Notion, Slack)
- [ ] Fixtures include all finding types: forgotten recurring charges, trial conversion, price increase, duplicate services, and renewal approaching
- [ ] Calling `updateFindingDecision` updates finding status (confirmed waste, marked useful, snoozed, dismissed) and adjusts potential vs confirmed savings in memory
- [ ] All mock methods return Promises with simulated latency (200ms–350ms) and execute zero outbound HTTP requests

### Out of scope
- Connecting to live FastAPI backend, moved to #20
- Live bank API OAuth integration, moved to #24

### Constraints
- Stay inside `frontend/src/services/` and `frontend/src/types/`
- Zero external backend dependencies or network requests

---

## 5. Dashboard Overview and Savings Metrics UI
Tag: `mvp`

### Goal
Build the dashboard Overview screen displaying high-level subscription metrics, upcoming renewals, and separated potential vs confirmed savings cards.

### Acceptance criteria
- [ ] Navigating to `/` displays summary metric cards: Monthly Recurring Spend, Active Subscriptions count, Potential Savings to Review, and Confirmed Realized Savings
- [ ] Potential savings and confirmed savings are displayed in separate visual containers and never combined into one misleading total
- [ ] Overview highlights top 3 urgent findings from the Waste Finder with quick action buttons
- [ ] Upcoming renewals widget lists subscriptions scheduled to charge in the next 14 days
- [ ] "Recently Detected Changes" feed displays alerts for recent price increases and trial conversions
- [ ] Displays loading skeleton placeholders while mock data loads

### Out of scope
- Full subscriptions data table, moved to #6
- Full waste finder management view, moved to #7

### Constraints
- Stay inside `frontend/src/pages/OverviewPage.tsx` and related components
- Consume data exclusively through `mockService.getOverviewMetrics()`

---

## 6. Subscriptions Table and Detail View UI
Tag: `mvp`

### Goal
Construct the Subscriptions table view and detail drawer displaying normalized vendors, cadence, amounts, evidence sources, and user status.

### Acceptance criteria
- [ ] Navigating to `/subscriptions` renders an interactive data table with columns: Vendor, Amount & Currency, Billing Cadence (Monthly, Annual), Last Charge Date, Next Expected Charge, Evidence Source Badge (Bank, Gmail, or Both), Confidence Score, and Status
- [ ] Status badges correctly render user state: `Needs Review`, `Useful`, `Potential Waste`, `Cancelled`
- [ ] Table supports text search filtering by vendor name and dropdown filtering by status and cadence
- [ ] Clicking a subscription row opens a detail slide-over drawer displaying linked transactions history and extracted email billing evidence
- [ ] User can manually override and edit vendor display name, cadence, and status from the detail drawer

### Out of scope
- Waste hypothesis card review, moved to #7
- Bank account reconnection flow, moved to #8

### Constraints
- Stay inside `frontend/src/pages/SubscriptionsPage.tsx` and `frontend/src/components/subscriptions/`
- Rely on `mockService.getSubscriptions()`

---

## 7. Waste Finder Review Cards and Action Workflow UI
Tag: `mvp`

### Goal
Build the Waste Finder screen presenting reviewable hypothesis cards with evidence rationale, confidence levels, and user action controls.

### Acceptance criteria
- [ ] Navigating to `/waste-finder` displays reviewable finding cards categorized by finding type: Forgotten Recurring Charge, Trial Conversion, Price Increase, Possible Duplicate, and Renewal Approaching
- [ ] Each card clearly displays: Finding Title, Plain-English Explanation ("Why this may matter"), Supporting Evidence (linked transactions / email snippets), Confidence Level, and Estimated Monthly/Annual Savings
- [ ] Every finding presents 4 explicit user actions: `Confirm Waste`, `Mark Useful`, `Snooze (30 days)`, and `Dismiss`
- [ ] Clicking an action updates the finding state, provides an undo toast notification, and updates the global savings tally
- [ ] A filter bar allows toggling between `Pending Review`, `Confirmed Waste`, and `Dismissed` findings
- [ ] When all pending findings have been reviewed, renders a clean zero-waste celebration banner

### Out of scope
- Automatic third-party cancellation of subscriptions, explicitly deferred per `_docs/plan.md`
- Exporting waste report to PDF/CSV, moved to #post-mvp

### Constraints
- Stay inside `frontend/src/pages/WasteFinderPage.tsx` and `frontend/src/components/waste/`
- Every finding must phrase conclusions as hypotheses, not authoritative product usage claims (per `_docs/plan.md`)

---

## 8. Connections and Data Privacy Controls UI
Tag: `mvp`

### Goal
Construct the Connections screen allowing users to view synthetic Bank and Gmail integration statuses, trigger manual data syncs, disconnect sources, and permanently delete imported data.

### Acceptance criteria
- [ ] Navigating to `/connections` displays connection cards for Bank Account and Gmail
- [ ] Each connection card shows: Connection Status (Connected / Disconnected), Last Successful Sync timestamp, Permission Scopes summary, and Disconnect button
- [ ] "Sync Now" button triggers simulated synchronization with animated progress bar and updates the last synced timestamp
- [ ] "Delete All Imported Data" button triggers a confirmation modal requiring explicit user confirmation before purging stored transactions and findings
- [ ] Clear privacy disclosures state what data is stored, encryption standards, and retention policies
- [ ] Disconnecting a source removes linked pending findings and updates UI status badges immediately

### Out of scope
- Real Plaid/TrueLayer bank OAuth link, moved to #24
- Real Google restricted-scope OAuth flow, moved to #25

### Constraints
- Stay inside `frontend/src/pages/ConnectionsPage.tsx` and `frontend/src/components/connections/`
- Follow data privacy and deletion guidelines in `_docs/plan.md` section 6 & 8

---

## 9. Renewals Timeline and Calendar View UI
Tag: `mvp`

### Goal
Build the Renewals screen presenting an upcoming charges timeline and calendar view to help users prevent surprise auto-charges.

### Acceptance criteria
- [ ] Navigating to `/renewals` displays a chronological timeline of expected upcoming charges grouped by time window (Next 7 Days, Next 30 Days, Later This Quarter)
- [ ] Each renewal item displays Vendor, Expected Charge Amount, Due Date, Cadence, and Supporting Evidence tag (e.g. "Predicted from 3 past monthly charges" or "Confirmed via Gmail invoice")
- [ ] Filter allows toggling between All Renewals and High-Spend Renewals (> $50/mo)
- [ ] Clicking a renewal item navigates directly to the corresponding Subscription detail view
- [ ] An "Add Reminder" toggle allows marking upcoming renewals for priority review

### Out of scope
- External email/SMS notification dispatchers, moved to #post-mvp

### Constraints
- Stay inside `frontend/src/pages/RenewalsPage.tsx` and `frontend/src/components/renewals/`
- Consume `mockService.getRenewals()`

---

# Phase 2: API Contract Definition

## 10. OpenAPI 3.0 Contract Specification
Tag: `mvp`

### Goal
Formulate the comprehensive OpenAPI 3.0 specification (`contract/openapi.yml`) detailing all endpoints, request bodies, query parameters, domain DTOs, and standardized error responses for the SubTracker API.

### Acceptance criteria
- [ ] File `contract/openapi.yml` exists and passes OpenAPI 3.0 linter validation without errors
- [ ] Fully documents endpoints:
  - `GET /api/overview`
  - `GET /api/subscriptions` & `GET /api/subscriptions/{id}` & `PATCH /api/subscriptions/{id}`
  - `GET /api/findings` & `POST /api/findings/{id}/action`
  - `GET /api/renewals`
  - `GET /api/connections` & `POST /api/connections/sync` & `POST /api/connections/{id}/disconnect`
  - `DELETE /api/user/data`
- [ ] Schemas defined: `SubscriptionResponse`, `FindingResponse`, `FindingActionRequest`, `TransactionResponse`, `BillingEvidenceResponse`, `ConnectionResponse`, `OverviewMetricsResponse`, `ErrorResponse`
- [ ] Parameter constraints, date-time formats, enums (`cadence`, `finding_type`, `user_decision`), and required attributes are fully specified
- [ ] Standardized HTTP status codes (200, 201, 204, 400, 404, 422) documented for all routes

### Out of scope
- Python backend route implementation, moved to #11 and #12

### Constraints
- Stay inside `contract/openapi.yml`
- Strictly vendor-agnostic OpenAPI 3.0.3 specification

---

# Phase 3: In-Memory Backend

## 11. Backend Scaffolding and In-Memory Domain Models
Tag: `mvp`

### Goal
Initialize the Python FastAPI backend project structure with Pydantic v2 schemas strictly mirroring `contract/openapi.yml` and establish the automated pytest harness.

### Acceptance criteria
- [ ] FastAPI application initializes in `backend/main.py` with CORS middleware configured for local frontend origin (`http://localhost:5173`)
- [ ] Pydantic v2 schemas in `backend/schemas/` mirror 100% of the DTO models in `contract/openapi.yml`
- [ ] Health check endpoint `GET /api/health` returns HTTP 200 with `{ "status": "ok" }`
- [ ] Running `pytest backend/tests/` passes with exit code 0
- [ ] Invalid request payloads to typed endpoints return HTTP 422 with structured field error messages

### Out of scope
- SQLite database connectivity, moved to #17
- Detection algorithm implementation, moved to #14

### Constraints
- Stay inside `backend/`
- Python 3.14 + FastAPI + Pydantic v2 + Pytest
- Strict schema parity with `contract/openapi.yml`

---

## 12. In-Memory Repositories and Subscription/Overview Endpoints
Tag: `mvp`

### Goal
Define abstract repository interfaces and thread-safe in-memory implementations, exposing the core Subscriptions and Overview REST API endpoints.

### Acceptance criteria
- [ ] `backend/repositories/base.py` defines abstract base classes: `SubscriptionRepository`, `FindingRepository`, `TransactionRepository`, `ConnectionRepository`
- [ ] `backend/repositories/memory.py` implements thread-safe in-memory storage using dict/list structures
- [ ] `GET /api/overview` calculates and returns real-time metrics (spend, counts, potential vs confirmed savings) from in-memory repositories
- [ ] `GET /api/subscriptions` supports query filtering by cadence and status with pagination
- [ ] `GET /api/subscriptions/{id}` and `PATCH /api/subscriptions/{id}` allow reading and updating subscription status/display name
- [ ] Integration tests in `backend/tests/test_subscriptions_api.py` verify all endpoints with 100% pass rate

### Out of scope
- Automated recurring charge detection engine, moved to #14
- Database persistence, moved to #17

### Constraints
- Stay inside `backend/repositories/` and `backend/routers/`
- Use FastAPI dependency injection (`Depends`) to decouple routers from storage

---

## 13. Synthetic Bank and Email Evidence Data Harness
Tag: `mvp`

### Goal
Develop a synthetic data generator providing realistic raw bank transactions and parsed email billing receipts for reproducible local testing without external API keys.

### Acceptance criteria
- [ ] `backend/services/synthetic_data.py` generates at least 25 realistic raw transaction records spanning 90 days across multiple merchants (AWS, GitHub, Figma, Adobe, Google Workspace)
- [ ] Transactions include variations: steady amounts, quiet price increases, trial conversions, and irregular charges
- [ ] Generator produces parsed billing evidence records (invoice emails, trial ending notices, price increase notices) matching transaction timestamps
- [ ] Exposes a `seed_synthetic_data(repositories)` utility function to populate in-memory or database repositories on demand
- [ ] Automated tests verify synthetic data generation consistency, currency formatting, and date interval validity

### Out of scope
- Real Plaid or Google API network requests, moved to #24 and #25

### Constraints
- Stay inside `backend/services/synthetic_data.py` and `backend/tests/test_synthetic_data.py`
- Zero external network dependencies or paid APIs

---

## 14. Merchant Normalization and Recurring Payment Detection Engine
Tag: `mvp`

### Goal
Build an explainable recurring-payment detection engine that normalizes raw merchant strings, detects payment intervals, and calculates subscription cadence and confidence.

### Acceptance criteria
- [ ] `backend/services/normalizer.py` normalizes noisy merchant strings (e.g., `AMZN MKTP US*2K389` -> `Amazon Web Services`, `GITHUB INC DIR DEP` -> `GitHub`)
- [ ] `backend/services/cadence.py` evaluates transaction intervals (weekly, monthly, annual) and determines payment regularity
- [ ] Engine groups transactions by normalized vendor and calculates: estimated amount, cadence, last charge date, and next expected charge
- [ ] Computes an explainable confidence score (0.0 to 1.0) and generates human-readable reasoning text
- [ ] Cross-references bank transactions with email billing evidence when matching vendor and amount exist
- [ ] Unit tests cover false positives: non-subscription recurring payments (transfers, payroll, one-off split payments) are correctly excluded

### Out of scope
- Waste hypothesis generation, moved to #15
- Black-box machine learning clustering models, explicitly deferred per `_docs/plan.md`

### Constraints
- Stay inside `backend/services/normalizer.py`, `backend/services/cadence.py`, and `backend/tests/`
- Every detected candidate must produce an explainable human-readable explanation

---

## 15. Waste Finder Hypothesis Engine and Savings Calculation
Tag: `mvp`

### Goal
Implement the Waste Finder hypothesis engine that scans subscriptions and evidence to identify forgotten charges, trial conversions, price increases, and potential duplicates.

### Acceptance criteria
- [ ] `backend/services/waste_detector.py` generates hypotheses for:
  - `forgotten_charge`: active recurring charge with no recent user review
  - `trial_conversion`: evidence of $0 introductory charge followed by paid recurring charges
  - `price_increase`: recurring charges where recent amount exceeds historical baseline
  - `possible_duplicate`: two active subscriptions sharing similar vendor category (e.g. Zoom and Google Meet)
  - `renewal_approaching`: annual or high-tier charge scheduled within 14 days
- [ ] Each finding computes `estimated_monthly_savings` and `estimated_annual_savings`
- [ ] Findings phrase outcomes strictly as hypotheses and cite underlying evidence references (transactions / receipts)
- [ ] Unit tests verify detection precision across all 5 finding types against synthetic datasets

### Out of scope
- Automatic service cancellation, deferred per `_docs/plan.md`

### Constraints
- Stay inside `backend/services/waste_detector.py` and `backend/tests/`
- Findings must never claim definitive "unused" status without verifiable evidence (per `_docs/plan.md`)

---

## 16. Waste Review Actions and Connections Endpoints
Tag: `mvp`

### Goal
Implement REST endpoints to review findings, trigger synthetic sync, disconnect connections, and delete user data.

### Acceptance criteria
- [ ] `GET /api/findings` returns all generated findings filterable by `user_decision` (`pending`, `confirmed_waste`, `marked_useful`, `snoozed`, `dismissed`)
- [ ] `POST /api/findings/{id}/action` records user decision, updates finding status, and recalculates potential vs confirmed savings
- [ ] `POST /api/connections/sync` triggers in-process sync using the synthetic data harness and runs detection pipeline
- [ ] `POST /api/connections/{id}/disconnect` sets connection status to disconnected
- [ ] `DELETE /api/user/data` purges all transactions, billing evidence, subscriptions, and findings from repositories
- [ ] Integration tests verify full review lifecycle and data deletion cleanliness

### Out of scope
- Live OAuth provider token refresh, moved to #24

### Constraints
- Stay inside `backend/routers/findings.py`, `backend/routers/connections.py`, and `backend/tests/`

---

# Phase 4: SQLite Database & SQLAlchemy 2.0 ORM Integration

## 17. SQLite Database Configuration and SQLAlchemy 2.0 Models
Tag: `mvp`

### Goal
Configure local SQLite database connectivity (`sqlite:///./app.db`) and declare DBMS-agnostic SQLAlchemy 2.0 ORM models for all SubTracker entities.

### Acceptance criteria
- [ ] `backend/database.py` initializes SQLAlchemy 2.0 engine targeting `sqlite:///./app.db` with WAL mode and `PRAGMA foreign_keys=ON`
- [ ] `backend/models.py` defines ORM models for `User`, `Connection`, `Transaction`, `BillingEvidence`, `Subscription`, `Finding`, and `Action` using typed `Mapped[...]` attributes
- [ ] Foreign keys and cascades are configured: deleting a user or connection cascades cleanly to transactions, evidence, and findings
- [ ] Unique constraints prevent duplicate transaction imports (`provider_connection_id` + `provider_transaction_id`)
- [ ] Automated test creates tables in an isolated test SQLite database and verifies relationship queries without vendor-locked SQL

### Out of scope
- Alembic migration scripts, moved to #18
- Swapping repository implementations, moved to #19

### Constraints
- Stay inside `backend/database.py`, `backend/models.py`, and `backend/tests/`
- Strictly local SQLite persistence (zero cloud databases, zero Postgres dependencies)
- Strictly DBMS-agnostic SQLAlchemy constructs

---

## 18. Alembic Database Migrations Setup
Tag: `mvp`

### Goal
Configure Alembic database migrations to provide version-controlled, declarative schema management for the local SQLite database.

### Acceptance criteria
- [ ] Alembic initialized in `backend/alembic/` with configuration in `backend/alembic.ini`
- [ ] `env.py` is configured with `render_as_batch=True` to support SQLite column and constraint alterations
- [ ] Initial migration script generated creating all 7 relational tables with primary keys, foreign keys, and indices
- [ ] Running `alembic upgrade head` on a fresh SQLite database builds schema cleanly
- [ ] Running `alembic downgrade base` removes all created tables without orphan errors
- [ ] Automated integration test runs migration upgrade and downgrade cycle successfully

### Out of scope
- Seed data migration, handled via synthetic harness #13

### Constraints
- Stay inside `backend/alembic/` and `backend/alembic.ini`
- Must configure SQLite batch mode for migration operations

---

## 19. SQLAlchemy Repositories Implementation
Tag: `mvp`

### Goal
Implement SQLite-backed SQLAlchemy repositories adhering to the abstract repository interfaces, swapping out in-memory repositories with zero controller changes.

### Acceptance criteria
- [ ] `backend/repositories/sqlalchemy.py` implements `SqlAlchemySubscriptionRepository`, `SqlAlchemyFindingRepository`, `SqlAlchemyTransactionRepository`, and `SqlAlchemyConnectionRepository`
- [ ] FastAPI dependency injection (`backend/dependencies.py`) binds SQLAlchemy repositories backed by scoped sessions
- [ ] Zero lines of router code or DTO schemas require modification during the repository swap
- [ ] All existing backend integration tests pass with 100% success rate against the SQLite database
- [ ] Data created via API calls persists across server restarts in `app.db`
- [ ] Database sessions are committed and closed cleanly on every HTTP request

### Out of scope
- Modifying frontend client, moved to #20

### Constraints
- Stay inside `backend/repositories/sqlalchemy.py` and `backend/dependencies.py`
- Adhere strictly to the abstract repository contracts from #12

---

# Phase 5: Full E2E Integration, Test Suite & QA Bug Hunting

## 20. Frontend API Client and Live Backend Integration
Tag: `mvp`

### Goal
Connect the React frontend to the live FastAPI backend, replacing `mockService` with an HTTP API client communicating over REST.

### Acceptance criteria
- [ ] `frontend/src/services/apiClient.ts` implements all API methods mirroring `mockService` over `fetch`
- [ ] Environment variable `VITE_API_URL` configures the backend endpoint (defaulting to `http://localhost:8000`)
- [ ] Dashboard views (Overview, Subscriptions, Waste Finder, Renewals, Connections) fetch and display live data from FastAPI
- [ ] Triggering "Sync Now" in the UI runs the backend detection pipeline and updates dashboard metrics in real time
- [ ] Reviewing a finding in Waste Finder persists the decision to SQLite and updates savings metrics
- [ ] HTTP error responses (400, 404, 422, 500) trigger user-friendly toast notifications in the UI

### Out of scope
- Multi-user authentication flows, moved to #post-mvp

### Constraints
- Stay inside `frontend/src/services/apiClient.ts` and UI page wiring
- Strict client-server decoupling over standard HTTP REST

---

## 21. End-to-End Integration Test Suite and Data Deletion Verification
Tag: `mvp`

### Goal
Build an automated end-to-end integration test suite verifying the complete flow from synthetic ingestion to waste detection, user review, and permanent data deletion.

### Acceptance criteria
- [ ] Automated test suite runs a complete lifecycle: ingest synthetic data -> run detection -> assert subscriptions identified -> assert findings generated
- [ ] Verifies finding actions: confirming waste adjusts confirmed savings; dismissing removes from active review
- [ ] Tests `DELETE /api/user/data` and asserts that SQLite tables (`transactions`, `billing_evidence`, `subscriptions`, `findings`) are completely purged
- [ ] Asserts that no sensitive raw email bodies or plain credentials remain in the database
- [ ] Entire test suite runs locally with a single command (`pytest backend/tests/test_e2e.py`) and passes with 0 failures

### Out of scope
- Performance load testing under 100,000+ transactions, moved to #post-mvp

### Constraints
- Stay inside `backend/tests/test_e2e.py`
- Must execute against local SQLite test database without external service mocks

---

## 22. Live Pilot Verification and QA Bug Hunting
Tag: `mvp`

### Goal
Execute comprehensive user testing of the integrated application, logging and resolving defects strictly under the `user-test-bug` protocol.

### Acceptance criteria
- [ ] Execute manual and automated user journeys across Overview, Subscriptions, Waste Finder, Renewals, and Connections
- [ ] Any defect or contract discrepancy found is cataloged as a GitHub issue tagged `user-test-bug` following the mandatory format: `Goal`, `Reproduction Steps`, `Observed Behavior`, `Expected Behavior`
- [ ] Every bug issue is groomed by PM and verified with test cases by QA before closing
- [ ] All `mvp` and `user-test-bug` issues are resolved and closed by `qa-engineer.md` before final release
- [ ] Zero unhandled errors in browser console or backend server logs during standard user journeys

### Out of scope
- Implementing post-MVP features, moved to #23, #24, #25

### Constraints
- Adhere strictly to the gatekeeper verification checklist in `team/qa-engineer.md`
- Final sign-off requires all `mvp` and `user-test-bug` issues to be closed

---

# Post-MVP Enhancements

## 23. CSV Bank Statement Import and Export
Tag: `post-mvp`

### Goal
Allow users to manually upload bank statement CSV files to discover subscriptions without connecting an external bank account, and export savings reports.

### Acceptance criteria
- [ ] User can upload CSV statements with column mapping for Date, Merchant, Amount, Currency
- [ ] Transactions are imported into local SQLite database and processed by detection engine
- [ ] User can export confirmed waste and savings summaries to CSV

### Out of scope
- Core MVP automated synthetic sync

### Constraints
- Client-side or backend CSV parsing without third-party cloud parser APIs

---

## 24. Live Bank Integration via Plaid / TrueLayer Adapter
Tag: `post-mvp`

### Goal
Implement a live bank connector adapter following the internal provider interface to ingest real transactions for a verified launch market.

### Acceptance criteria
- [ ] Implement `BankAdapter` interface with `connect()`, `syncTransactions()`, `disconnect()`
- [ ] Securely store OAuth tokens encrypted at rest using AES-256-GCM
- [ ] Handle consent expiration, webhook notifications, and incremental sync

### Out of scope
- Supporting multiple countries simultaneously before validating one launch market

### Constraints
- Keep provider adapter decoupled from internal detection engine per `_docs/plan.md`

---

## 25. Real Google OAuth and Restricted-Scope Gmail Sync
Tag: `post-mvp`

### Goal
Integrate live Gmail API with restricted scope `gmail.readonly` for automatic invoice and renewal receipt discovery following Google security policies.

### Acceptance criteria
- [ ] Implement Google OAuth 2.0 flow with minimal requested scopes
- [ ] Search query targets only billing-related emails (`has:attachment`, keywords `invoice`, `receipt`, `subscription`, `renewal`)
- [ ] Store minimal extracted metadata (vendor, amount, date), avoiding raw email body retention
- [ ] Token encryption at rest and immediate data purge on disconnect

### Out of scope
- Full inbox AI summarization

### Constraints
- Adhere strictly to Google API Services User Data Policy and security assessment guidelines in `_docs/plan.md` section 6
