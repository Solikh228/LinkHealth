# SubTracker Frontend

Client application for **SubTracker** (Hidden B2B Subscriptions & Waste Finder Tracker), built with TanStack Start, React 19, TypeScript, and Tailwind CSS.

> **API & Architecture Specification:** For the complete REST contract, DTO schemas, and endpoint definitions, see [docs/spec.md](../docs/spec.md).

## Features
- **Dashboard Overview (`/`):** Summary spend metrics, potential savings breakdown, upcoming renewals, and spend by category.
- **Subscriptions (`/subscriptions`):** Filterable table with cadence, last charges, linked transactions, and email receipts.
- **Waste Finder (`/findings`):** Reviewable waste hypotheses with trigger evidence, confidence levels, and user decision actions.
- **Integrations (`/integrations`):** Bank and Gmail connection management, sync triggers, and privacy/deletion controls.
- **Dual API Modes:** Run standalone with built-in mock fixtures (`VITE_API_MODE=mock`) or connected to the FastAPI backend (`VITE_API_MODE=http`).

## Development

```sh
# Install dependencies
npm install

# Run development server
npm run dev

# Run test suite
npm test

# Build for production
npm run build
```
