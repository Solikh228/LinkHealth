export type Money = {
  amountMinor: number;
  currency: string;
};

export type ConnectionStatus = "connected" | "syncing" | "error" | "disconnected";

export interface Connection {
  id: string;
  name: string;
  type: "bank" | "email";
  provider: string;
  status: ConnectionStatus;
  lastSyncedAt: string;
  accountMask?: string;
  emailAddress?: string;
}

export type BillingInterval = "monthly" | "annual" | "quarterly" | "weekly" | "irregular";

export interface BillingEvidence {
  id: string;
  subscriptionId: string;
  senderDomain: string;
  subject: string;
  receivedAt: string;
  snippet: string;
  extractedAmountMinor?: number;
  confidence: number;
}

export interface Subscription {
  id: string;
  name: string;
  vendorDomain?: string;
  category: string;
  status: "active" | "candidate" | "confirmed" | "dismissed" | "cancelled";
  billingInterval: BillingInterval;
  amount: Money;
  monthlyEquivalent: Money;
  nextRenewalDate?: string;
  confidence: number;
  explanation: string;
  lastChargeDate: string;
}

export interface Renewal {
  id: string;
  subscriptionId: string;
  vendorName: string;
  amount: Money;
  dueDate: string;
  cadence: BillingInterval;
  evidenceTag: string;
  hasReminder: boolean;
  timeWindow: "next_7_days" | "next_30_days" | "later_this_quarter";
}

export type FindingType =
  | "forgotten_charge"
  | "trial_conversion"
  | "price_increase"
  | "duplicate_service"
  | "renewal_approaching";

export type FindingDecision = "confirmed_waste" | "marked_useful" | "snoozed" | "dismissed";

export interface Finding {
  id: string;
  subscriptionId: string;
  subscriptionName: string;
  type: FindingType;
  severity: "low" | "medium" | "high";
  status: "open" | FindingDecision;
  title: string;
  explanation: string;
  potentialSavings: Money;
  confirmedSavings?: Money;
  decision?: FindingDecision;
  decisionNote?: string;
  decisionAt?: string;
  evidence: BillingEvidence[];
  createdAt: string;
}

export interface Transaction {
  id: string;
  subscriptionId?: string;
  connectionId: string;
  accountName: string;
  date: string;
  descriptionRaw: string;
  merchantNormalized?: string;
  amount: Money;
  status: "posted" | "pending";
  isRecurringCandidate: boolean;
}

export interface OverviewMetrics {
  monthlyRecurringSpend: Money;
  annualizedSpend: Money;
  activeSubscriptionCount: number;
  potentialSavings: Money;
  confirmedSavings: Money;
  openFindingsCount: number;
  upcomingRenewalsCount: number;
}
