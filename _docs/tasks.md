# LinkHealth Backlog

This backlog outlines the step-by-step tasks required to build LinkHealth following the strict 5-phase iterative roadmap. Each task is self-contained, scoped for a single focused session, and adheres to the project template.

---

## 1. Project Scaffolding and Smoke Test Setup
Goal: Establish an initial project repository structure with automated test execution and a passing smoke test.
Description: Initialize the root repository workspace with separated directories for frontend and backend applications alongside configuration files. Configure a basic test runner in the repository that executes a trivial smoke test verifying the testing harness is functional. Ensure that the test suite can be run with a single command and passes successfully in a clean environment.

## 2. Repository Governance and Role Workflow Documentation
Goal: Create standard role governance files and workflow instructions at the repository root.
Description: Author `pm.md`, `architect.md`, `qa-engineer.md`, and `brainstorm_chat_history.md` outlining project requirements, system architecture, test criteria, and historical scope decisions. Define the GitHub issue lifecycle including the mandatory templates and usage guidelines for tags `mvp`, `post-mvp`, and `user-test-bug`. Establish the formal gatekeeper criteria required by the QA role to verify and close bug issues before final submission.

## 3. Frontend Application Setup with Tailwind CSS and Component Library
Goal: Scaffold the React TypeScript frontend application with styling and baseline UI primitives.
Description: Initialize a React application using Vite and TypeScript in the `frontend` directory with Tailwind CSS configured. Install and configure Lucide icons alongside base shadcn/ui component utilities for layouts, buttons, and typography. Verify the setup by serving the development server locally and rendering an initial LinkHealth dashboard placeholder layout.

## 4. Frontend Mock Service and Synthetic Fixtures
Goal: Implement an isolated frontend mock service providing realistic fixture data for offline execution.
Description: Create `mockService.ts` containing realistic synthetic data fixtures for projects, audit runs, and link check results across various HTTP statuses such as 200, 404, 500, and 301. Implement mock asynchronous methods that simulate network latency, pagination, filtering, and error scenarios. Ensure the mock layer allows the entire frontend application to function offline without a running backend.

## 5. Projects Dashboard and Creation Modal UI
Goal: Build the project management dashboard view and project creation modal using mock data.
Description: Implement a responsive project list view that displays target websites, creation timestamps, and overall health summaries using mock data. Build a project creation dialog with input validation to ensure entered target URLs are well-formed before adding them to state. Wire the creation workflow to the mock service and provide instant feedback using toast notifications.

## 6. Audit History Table and Run Trigger UI
Goal: Build the project audit history list and manual audit trigger workflow on the project details view.
Description: Construct a project details page displaying metadata, cumulative health score metrics, and a historical table of previous audit runs. Implement an "Audit Now" button that triggers an in-progress audit state with animated progress indicators and simulated polling. Update the run status dynamically from PENDING to IN_PROGRESS to COMPLETED using mock service responses.

## 7. Audit Run Detail View and Link Results Inspector
Goal: Build the detailed inspection screen displaying link check results with status filters and search.
Description: Create an audit run detail view featuring a visual health score gauge, summary cards for total links, broken links, and average latency. Implement an interactive data table displaying inspected URLs, HTTP status codes, response times, anchor text, and failure messages. Add client-side filtering by HTTP status class (2xx, 3xx, 4xx, 5xx) and a text search bar for target URLs and anchor text.

## 8. Regression Diff View UI
Goal: Build the audit regression comparison view showing newly broken and resolved links between runs.
Description: Create a comparison view that allows users to select two audit runs for a project and inspect regressions over time. Render categorized lists highlighting links that were healthy in the baseline run but failed in the target run, as well as newly fixed links. Provide clear visual cues and badges indicating the health score delta and regression count between the selected runs.

## 9. OpenAPI 3.0 Contract Specification
Goal: Formulate the complete OpenAPI 3.0 contract file defining all LinkHealth REST endpoints and schemas.
Description: Create `contract/openapi.yml` as the single source of truth defining data models including `Project`, `AuditRun`, `LinkCheckResult`, and `DiffResult`. Document all REST operations including project CRUD, audit triggering, run status inspection, link result retrieval, and run comparison diffs. Include explicit request validation rules, query parameters, and standardized HTTP error response envelopes.

## 10. Backend Scaffolding and In-Memory Domain Models
Goal: Set up the Python FastAPI backend application with domain entities and test configuration.
Description: Scaffold the backend application directory with FastAPI, Pydantic v2, and a `pytest` testing configuration. Define core Pydantic domain models and DTO schemas strictly mirroring the schemas documented in `contract/openapi.yml`. Implement a basic API health check endpoint and write an automated test to confirm the FastAPI server launches and passes tests.

## 11. In-Memory Repositories and Project REST API
Goal: Implement abstract repository interfaces, in-memory storage implementations, and project management API routes.
Description: Define abstract repository base classes for projects and audit records, followed by thread-safe in-memory dictionary implementations. Implement the FastAPI route handlers for `GET /api/projects`, `POST /api/projects`, `GET /api/projects/{id}`, and `DELETE /api/projects/{id}` using the repository interfaces. Write comprehensive unit and integration tests verifying project creation, retrieval, duplicate validation, and deletion against the in-memory store.

## 12. Local HTML Link Extraction and Normalization Service
Goal: Build a zero-dependency HTML parser service to extract and normalize hyperlinks from landing pages.
Description: Develop a service using `beautifulsoup4` and standard `urllib.parse` that parses raw HTML content and extracts all anchor tags (`<a href>`). Normalize relative URLs to absolute URLs against the base target address while filtering out unsupported schemes like `mailto:`, `tel:`, and `javascript:`. Strip URL fragments (`#section`) to prevent duplicate checks and write unit tests covering standard, relative, malformed, and edge-case URLs.

## 13. Asynchronous HTTP Link Checker Service
Goal: Implement an asynchronous concurrent link inspection engine with rate limiting and timeout handling.
Description: Build a link checking service using `httpx.AsyncClient` that checks candidate URLs concurrently while limiting simultaneous outbound requests via an `asyncio.Semaphore`. Capture response status codes, round-trip response times in milliseconds, redirect destinations, and network timeout errors. Write unit tests mocking external HTTP targets to verify correct classification of broken versus healthy links and graceful handling of unreachable hosts.

## 14. Audit Execution Orchestrator and Run Endpoints
Goal: Connect link extraction and checking into an audit execution service exposed via REST endpoints.
Description: Implement an in-process audit orchestrator that fetches a target website, extracts hyperlinks, checks each link concurrently, computes the aggregate health score, and stores the results. Implement FastAPI route handlers for `POST /api/projects/{id}/run`, `GET /api/runs/{id}`, and `GET /api/runs/{id}/results`. Write integration tests verifying that triggering an audit transitions the run status through its lifecycle and stores all individual link outcomes.

## 15. Audit Regression Diff Computation and Endpoint
Goal: Implement the regression comparison algorithm and expose the diff endpoint over REST.
Description: Create a diff computation utility that compares link check results across two distinct audit runs for the same project. Identify regression links that transitioned from successful to broken, fixed links that recovered, and recurring persistent failures. Implement the `GET /api/runs/{id}/diff` endpoint and write unit tests validating accurate delta calculations and regression classifications.

## 16. SQLite Database Configuration and SQLAlchemy 2.0 Models
Goal: Configure SQLite database connectivity and define DBMS-agnostic SQLAlchemy ORM models.
Description: Establish an engine connection string targeting the local `app.db` file using SQLAlchemy 2.0 without vendor-locked SQL dialects. Define ORM table mappings for `projects`, `audit_runs`, and `link_check_results` using foreign keys and cascading relationships. Write an automated test confirming that the database engine initializes, connects to the SQLite file, and creates tables successfully.

## 17. Alembic Database Migrations Setup
Goal: Configure Alembic migrations for declarative version control of the SQLite database schema.
Description: Initialize and configure Alembic within the backend directory linked to the SQLAlchemy metadata and SQLite database URI. Generate an initial baseline migration script that creates all LinkHealth relational tables, foreign key constraints, and indices. Write a verification script or test to apply and roll back migrations cleanly against an isolated test database file.

## 18. SQLAlchemy Repositories Implementation
Goal: Implement database-backed repositories adhering to the abstract repository interfaces.
Description: Implement `SqlAlchemyProjectRepository`, `SqlAlchemyAuditRunRepository`, and `SqlAlchemyLinkCheckResultRepository` utilizing SQLAlchemy 2.0 session queries. Swap the FastAPI dependency injection bindings from in-memory repositories to SQLAlchemy repositories without modifying API controller logic or DTO schemas. Execute the existing backend test suite to verify that all API endpoints function identically with persistent database storage.

## 19. Frontend API Client and Live Backend Integration
Goal: Replace the frontend mock service with an HTTP client connected to the running backend.
Description: Implement an API client layer in the frontend using standard `fetch` or Axios configured to communicate with the FastAPI server endpoints. Update state management and UI hooks to fetch real project records, initiate live audit runs, and retrieve real link results from the backend. Verify that the user interface seamlessly handles real-world network latency, in-flight loading states, and backend error responses.

## 20. End-to-End Audit Verification and Bug Hunting Protocol
Goal: Execute full end-to-end audit runs against real target websites and log defects using the bug workflow.
Description: Run comprehensive end-to-end audit flows using the integrated stack against live landing pages and mock broken documentation sites. Validate that discovered anomalies or regressions are cataloged as issues using the `user-test-bug` template with complete reproduction steps. Coordinate fixes through the `pm.md` and `qa-engineer.md` workflows, ensuring all test cases pass before final sign-off.
