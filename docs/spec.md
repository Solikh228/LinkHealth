# SubTracker API & Application Specification

**Version:** 1.0.0  
**Status:** Canonical Frontend-Backend Contract  
**Reference Document:** Derived from `_docs/plan.md` and `frontend/src/lib/api/`  

---

## 1. Executive Summary & Architecture

SubTracker is a micro-SaaS web application for freelancers, independent consultants, and solo business owners to discover forgotten recurring expenses, understand subscription commitments, and review potential waste.

### Architecture Principles
- **Strict Decoupling:** The frontend and backend communicate exclusively via standard HTTP REST requests.
- **Offline Mock Capability:** The frontend supports both local offline mock execution (`VITE_API_MODE=mock`) and live REST backend communication (`VITE_API_MODE=http`).
- **Local Persistence:** The backend persists data to a local SQLite database (`sqlite:///./app.db`) managed via SQLAlchemy 2.0 without external cloud database dependencies.
- **Money Representation:** Financial values are strictly represented as integer minor units (e.g. cents, pence) alongside a 3-letter ISO-4217 currency code (`{ amountMinor: 2900, currency: "USD" }`).

---

## 2. API Contract & Endpoints

All endpoints accept and return `application/json`. Authenticated routes expect an `Authorization: Bearer <token>` header. Non-GET mutation requests include a client-generated `Idempotency-Key` header.

### 2.1 Authentication & Workspace
| Method | Endpoint | Request Body | Response Body | Description |
|---|---|---|---|---|
| `POST` | `/auth/session` | `{ email, password }` | `{ token: string, user: User }` | Authenticate or initialize user session |
| `GET` | `/me` | None | `User` | Retrieve current authenticated user profile |
| `GET` | `/workspace` | None | `Workspace` | Retrieve active workspace configuration and base currency |
| `DELETE` | `/account` | None | `204 No Content` | Purge all user account data, transactions, and findings |

### 2.2 Integrations & Connections
| Method | Endpoint | Request Body | Response Body | Description |
|---|---|---|---|---|
| `GET` | `/integrations` | None | `IntegrationConnection[]` | List configured bank and email integrations |
| `POST` | `/integrations/bank/connect` | `{}` | `{ redirectUrl: string \| null, connection: IntegrationConnection }` | Initiate bank connection flow (synthetic or provider OAuth) |
| `POST` | `/integrations/gmail/connect` | `{}` | `{ redirectUrl: string \| null, connection: IntegrationConnection }` | Initiate email evidence connection flow |
| `POST` | `/integrations/{id}/sync` | `{}` | `IntegrationConnection` | Trigger in-process sync and analysis pipeline |
| `POST` | `/integrations/{id}/disconnect` | `{ deleteData: boolean }` | `204 No Content` | Disconnect integration and optionally purge imported data |

### 2.3 Dashboard & Overview
| Method | Endpoint | Query Parameters | Response Body | Description |
|---|---|---|---|---|
| `GET` | `/dashboard/summary` | None | `DashboardSummary` | Aggregate monthly recurring spend, potential savings, and changes |

### 2.4 Transactions
| Method | Endpoint | Query Parameters | Response Body | Description |
|---|---|---|---|---|
| `GET` | `/transactions` | `q?: string, status?: TransactionStatus, page?: number, pageSize?: number` | `Paginated<Transaction>` | Paginated list of raw and normalized transactions |

### 2.5 Subscriptions
| Method | Endpoint | Query Parameters | Response Body | Description |
|---|---|---|---|---|
| `GET` | `/subscriptions` | None | `Subscription[]` | Retrieve all detected subscription candidates and confirmed items |
| `GET` | `/subscriptions/{id}` | None | `SubscriptionDetail` | Detailed subscription view with linked transactions and evidence |
| `PATCH` | `/subscriptions/{id}` | `SubscriptionPatch` | `Subscription` | Update subscription attributes (status, cadence, displayName, note) |
| `POST` | `/subscriptions/{id}/confirm` | `{}` | `Subscription` | Confirm candidate as an active business subscription |
| `POST` | `/subscriptions/{id}/dismiss` | `{}` | `Subscription` | Dismiss subscription candidate from active tracking |

### 2.6 Findings & Waste Review
| Method | Endpoint | Query Parameters | Response Body | Description |
|---|---|---|---|---|
| `GET` | `/findings` | `status?: FindingStatus, type?: FindingType` | `Finding[]` | Retrieve all reviewable waste findings |
| `GET` | `/findings/{id}` | None | `FindingDetail` | Detailed finding view with trigger/supporting evidence items |
| `POST` | `/findings/{id}/review` | `ReviewInput` | `FindingDetail` | Submit user decision (`confirm`, `dismiss`, `mark_reviewing`, `resolve`) |

---

## 3. Data Models & Entity Schemas

### 3.1 Financial Primitive (`Money`)
```typescript
export interface Money {
  amountMinor: number; // e.g., 2900 for $29.00
  currency: string;    // ISO 4217 code (USD, EUR, GBP)
}
```

### 3.2 Core Domain Models

```typescript
export interface User {
  id: string;
  email: string;
  createdAt: string;
}

export interface Workspace {
  id: string;
  name: string;
  ownerUserId: string;
  baseCurrency: string;
  createdAt: string;
}

export type ConnectionStatus = "pending" | "active" | "needs_reauth" | "error" | "disconnected";
export type SyncState = "not_connected" | "connecting" | "initial_sync" | "up_to_date" | "delayed" | "needs_reauth" | "error" | "disconnected";

export interface IntegrationConnection {
  id: string;
  kind: "bank" | "gmail";
  provider: string; // "synthetic", "plaid", "truelayer", "google"
  displayName: string;
  status: ConnectionStatus;
  syncState: SyncState;
  scopesGranted: string[];
  lastSyncAt: string | null;
  lastSyncStatus: "success" | "failed" | "running" | null;
  createdAt: string;
}

export type TransactionStatus = "pending" | "posted" | "reversed" | "removed";

export interface Transaction {
  id: string;
  connectionId: string;
  accountName: string;
  postedAt: string;
  amount: Money;
  descriptionRaw: string;
  merchantNormalized: string | null;
  status: TransactionStatus;
  isRecurringCandidate: boolean;
  subscriptionId: string | null;
}

export type BillingInterval = "weekly" | "monthly" | "quarterly" | "annual" | "irregular" | "unknown";
export type SubscriptionStatus = "candidate" | "confirmed" | "dismissed" | "inactive";

export interface Subscription {
  id: string;
  vendorName: string;
  vendorDomain: string | null;
  category: string | null;
  displayName: string;
  status: SubscriptionStatus;
  billingInterval: BillingInterval;
  expectedAmount: Money | null;
  monthlyEquivalent: Money | null;
  estimatedNextChargeAt: string | null;
  detectionConfidence: number; // 0.0 to 1.0
  detectionExplanation: string;
  lastDetectedAt: string;
  note: string | null;
}

export type EvidenceType = "invoice" | "receipt" | "renewal" | "cancellation" | "other";

export interface EmailEvidence {
  id: string;
  receivedAt: string;
  senderDomain: string | null;
  subjectMinimized: string | null;
  evidenceType: EvidenceType;
  amount: Money | null;
  invoiceDate: string | null;
  extractionConfidence: number;
  matchScore: number;
  matchStatus: "suggested" | "confirmed" | "rejected";
  matchReason: string;
}

export interface SubscriptionDetail extends Subscription {
  transactions: Transaction[];
  evidence: EmailEvidence[];
  findings: Finding[];
}

export type FindingType =
  | "possible_duplicate"
  | "price_increase"
  | "unexpected_charge"
  | "low_evidence"
  | "renewal_approaching"
  | "unclear_vendor";

export type FindingStatus = "new" | "reviewing" | "confirmed" | "dismissed" | "resolved";
export type Severity = "low" | "medium" | "high";

export interface Finding {
  id: string;
  subscriptionId: string | null;
  subscriptionName: string | null;
  findingType: FindingType;
  severity: Severity;
  status: FindingStatus;
  title: string;
  explanation: string;
  estimatedImpact: Money | null;
  confidence: number;
  ruleVersion: string;
  createdAt: string;
  updatedAt: string;
}

export interface FindingEvidenceItem {
  role: "trigger" | "supporting" | "context";
  explanation: string;
  transaction?: Transaction;
  email?: EmailEvidence;
}

export interface UserReview {
  id: string;
  decision: "confirm" | "dismiss" | "mark_reviewing" | "resolve";
  note: string | null;
  estimatedSavings: Money | null;
  createdAt: string;
}

export interface FindingDetail extends Finding {
  evidence: FindingEvidenceItem[];
  reviews: UserReview[];
}

export interface DashboardSummary {
  monthlyRecurringSpend: Money;
  annualizedSpend: Money;
  subscriptionCount: number;
  candidateCount: number;
  openFindingsCount: number;
  potentialSavings: Money;
  userEstimatedSavings: Money;
  upcoming: { subscriptionId: string; name: string; date: string; amount: Money | null }[];
  recentChanges: { subscriptionId: string; name: string; kind: "new" | "price_change"; date: string; detail: string }[];
  spendByCategory: { category: string; monthly: Money }[];
  connections: IntegrationConnection[];
}
```

---

## 4. Client Route Structure (Frontend)

The frontend application uses TanStack Start / TanStack Router file-based routing:

| Route Path | File Location | Purpose |
|---|---|---|
| `/` | `src/routes/index.tsx` | Dashboard overview: metrics, upcoming renewals, category breakdown |
| `/subscriptions` | `src/routes/subscriptions.index.tsx` | Full subscriptions table with cadence and status filters |
| `/subscriptions/:id` | `src/routes/subscriptions.$id.tsx` | Detailed subscription view with linked transactions and email receipts |
| `/findings` | `src/routes/findings.index.tsx` | Waste Finder view listing candidate hypotheses for review |
| `/findings/:id` | `src/routes/findings.$id.tsx` | Detailed finding view with trigger evidence and review decision action |
| `/integrations` | `src/routes/integrations.tsx` | Manage Bank and Gmail connections, sync state, and data purge |
| `/transactions` | `src/routes/transactions.tsx` | Searchable transaction feed |
| `/settings` | `src/routes/settings.tsx` | User preferences, workspace currency, and account deletion |
| `/login` | `src/routes/login.tsx` | Session authentication screen |
| Root Shell | `src/routes/__root.tsx` | Top navigation bar, theme provider, and global error boundaries |

---

## 5. Environment Variables & Mode Switching

The frontend connects to the backend through environment variables configured in `frontend/.env`:

```bash
# Set API operational mode: 'mock' for in-memory offline execution, 'http' for live REST backend
VITE_API_MODE=http

# Backend base URL when in http mode
VITE_API_BASE_URL=http://localhost:8000/api
```
