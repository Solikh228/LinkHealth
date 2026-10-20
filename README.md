# SubTracker — Hidden B2B Subscriptions & Auto-Charge Tracker

SubTracker helps businesses uncover hidden recurring subscriptions, price increases, forgotten tools, and duplicate software licenses from synthetic bank feeds and email evidence.

## Architecture

- **`frontend/`**: Vite + React + TypeScript + Tailwind CSS application.
- **`backend/`**: FastAPI REST backend using SQLAlchemy and SQLite (database-agnostic).
- **`contract/`**: OpenAPI 3.0 contract specification.
- **`_docs/`**: Product requirements, specifications, and architecture plans.
- **`tests/`**: Repository root smoke tests and system sanity checks.

## Quick Start

### Prerequisites
- Python 3.10+ (uv recommended)
- Node.js 18+ (npm)

### Running Locally

```bash
# Start backend (port 8091)
cd backend
uv run uvicorn backend.main:app --reload --port 8091

# Start frontend (port 5173 / 3000)
cd frontend
npm run dev
```

Or using Make:
```bash
make run   # or .\make.cmd run on Windows
```

### Running Tests

```bash
# Root smoke test
python -m pytest

# Backend test suite
cd backend && uv run pytest

# Frontend test suite
cd frontend && npm test -- --run
```
