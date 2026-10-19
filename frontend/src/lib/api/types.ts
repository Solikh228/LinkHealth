// Types mirror the spec's API/data model (section 8 & 10). Money is always integer minor units + ISO currency.

export type Money = { amountMinor: number; currency: string };

export type ConnectionStatus = "pending" | "active" | "needs_reauth" | "error" | "disconnected";
export type SyncState =
  | "not_connected"
  | "connecting"
  | "initial_sync"
  | "up_to_date"
  | "delayed"
  | "needs_reauth"
  | "error"
  | "disconnected";

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

export interface IntegrationConnection {
  id: string;
  kind: "bank" | "gmail";
  provider: string; // e.g. "plaid", "truelayer", "google"
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
  detectionConfidence: number; // 0..1
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

export interface Paginated<T> {
  items: T[];
  nextCursor: string | null;
  total: number;
}

export interface ReviewInput {
  decision: UserReview["decision"];
  note?: string | undefined;
  estimatedSavings?: Money | undefined;
}

export interface SubscriptionPatch {
  displayName?: string;
  billingInterval?: BillingInterval;
  expectedAmount?: Money;
  category?: string;
  note?: string | undefined;
}

export interface TransactionQuery {
  search?: string;
  recurringOnly?: boolean;
  cursor?: string;
  limit?: number;
}

export interface FindingQuery {
  status?: FindingStatus | "open" | undefined;
  type?: FindingType;
}
