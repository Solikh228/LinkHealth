# Product Brainstorming & Architecture History

## Background & Customer Discovery
SubTracker was conceived to solve the hidden SaaS auto-charge problem for solo entrepreneurs, freelancers, and small businesses. Unlike large enterprise procurement teams, solo business owners often accumulate $500–$2,000/month in SaaS subscriptions without noticing annual auto-renewals, duplicate design/productivity licenses, forgotten developer utilities, and subtle price hikes.

## Core Positioning Decisions
1. **Target User**: Solo founder, freelancer, or boutique digital agency.
2. **Key Distinction**: "Hypothesis engine, not a cancellation bot." The software presents evidence-backed findings rather than claiming certainty about whether a user actively uses a tool.
3. **Data Sources**:
   - Financial transactions (debit/credit card bank feed descriptors)
   - Email evidence (invoice receipts, renewal reminders, price change notices)
4. **Trust & Privacy First**:
   - Zero external SaaS database dependencies. Everything runs locally or within private infrastructure.
   - Comprehensive account purge: `DELETE /account` permanently deletes all imported transactions, email snippets, and findings.

## Scope Trade-Offs (MVP vs Post-MVP)
- **MVP Scope**:
  - Synthetic bank feed and Gmail evidence harness providing deterministic data.
  - Subscription detection engine analyzing transaction periodicity and variance.
  - Rule-based hypothesis engine:
    - Possible duplicate tools (e.g. Adobe Creative Cloud vs Figma)
    - Price increases (e.g. Notion $10 -> $12)
    - Approaching renewals (e.g. annual domain renewal in 12 days)
    - Low-evidence / forgotten tools
    - Unclear vendor descriptors (e.g. PayPal *DGTLSRV)
  - Full React UI: Dashboard overview, Subscriptions list/detail, Waste Finder review cards, Renewals timeline, Connections management.
  - SQLite local database via SQLAlchemy ORM.
- **Post-MVP Scope**:
  - Live Plaid / TrueLayer Open Banking OAuth credentials.
  - Live Google Workspace OAuth read integration.
  - Multi-seat workspace billing and team role-based access control.
