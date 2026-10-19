import type { ApiClient } from "./client";
import type {
  EmailEvidence,
  Finding,
  FindingDetail,
  IntegrationConnection,
  Money,
  Subscription,
  Transaction,
  UserReview,
} from "./types";
import { monthlyEquivalentMinor } from "../money";

// In-memory mock backend. State lives per browser tab and resets on reload.
const delay = (ms = 250 + Math.random() * 350) => new Promise((r) => setTimeout(r, ms));
const uid = (p: string) => `${p}_${Math.random().toString(36).slice(2, 10)}`;
const usd = (amountMinor: number): Money => ({ amountMinor, currency: "USD" });
const eur = (amountMinor: number): Money => ({ amountMinor, currency: "EUR" });
const clone = <T,>(v: T): T => structuredClone(v);

const NOW = new Date("2026-10-19T12:00:00Z");
const daysAgo = (d: number) => new Date(NOW.getTime() - d * 864e5).toISOString();
const daysAhead = (d: number) => new Date(NOW.getTime() + d * 864e5).toISOString();

const user = { id: "usr_1", email: "alex@studio.dev", createdAt: daysAgo(400) };
const workspace = { id: "ws_1", name: "Alex Studio", ownerUserId: user.id, baseCurrency: "USD", createdAt: daysAgo(400) };

let connections: IntegrationConnection[] = [
  {
    id: "conn_bank",
    kind: "bank",
    provider: "plaid",
    displayName: "Chase Business ••4821",
    status: "active",
    syncState: "up_to_date",
    scopesGranted: ["transactions:read", "accounts:read"],
    lastSyncAt: daysAgo(0.1),
    lastSyncStatus: "success",
    createdAt: daysAgo(120),
  },
  {
    id: "conn_gmail",
    kind: "gmail",
    provider: "google",
    displayName: "alex@studio.dev",
    status: "needs_reauth",
    syncState: "needs_reauth",
    scopesGranted: ["gmail.readonly"],
    lastSyncAt: daysAgo(6),
    lastSyncStatus: "failed",
    createdAt: daysAgo(120),
  },
];

type Seed = {
  id: string;
  name: string;
  domain: string;
  category: string;
  interval: Subscription["billingInterval"];
  amounts: number[]; // oldest -> newest, minor units
  currency?: "USD" | "EUR";
  descriptor: string;
  status: Subscription["status"];
  confidence: number;
  explanation: string;
  nextIn: number | null;
  everyDays: number;
};

const seeds: Seed[] = [
  { id: "sub_figma", name: "Figma Professional", domain: "figma.com", category: "Design", interval: "monthly", amounts: [1500, 1500, 1500, 1500, 1500, 1500], descriptor: "FIGMA *MONTHLY SAN FRANCISCO", status: "confirmed", confidence: 0.97, explanation: "6 charges ~30 days apart, identical amount, matched to 6 invoice emails from figma.com.", nextIn: 8, everyDays: 30 },
  { id: "sub_notion", name: "Notion Plus", domain: "notion.so", category: "Productivity", interval: "monthly", amounts: [1000, 1000, 1000, 1200, 1200, 1200], descriptor: "NOTION LABS INC", status: "candidate", confidence: 0.91, explanation: "Monthly cadence (±2 days). Amount rose from $10.00 to $12.00 three cycles ago.", nextIn: 3, everyDays: 30 },
  { id: "sub_aws", name: "Amazon Web Services", domain: "aws.amazon.com", category: "Infrastructure", interval: "monthly", amounts: [4210, 3988, 5120, 4475, 4630, 4902], descriptor: "AWS EMEA aws.amazon.co", status: "confirmed", confidence: 0.88, explanation: "Variable usage-based amounts, consistent monthly cadence on the 2nd–3rd.", nextIn: 14, everyDays: 30 },
  { id: "sub_adobe", name: "Adobe Creative Cloud", domain: "adobe.com", category: "Design", interval: "monthly", amounts: [5499, 5499, 5499, 5999, 5999, 5999], descriptor: "ADOBE *CREATIVE CLD", status: "candidate", confidence: 0.94, explanation: "Monthly cadence. Overlaps with Figma Professional in the Design category.", nextIn: 11, everyDays: 30 },
  { id: "sub_domain", name: "Namecheap domains", domain: "namecheap.com", category: "Domains", interval: "annual", amounts: [3298, 3498], descriptor: "NAMECHEAP.COM*RENEW", status: "candidate", confidence: 0.79, explanation: "Two charges ~365 days apart with renewal emails.", nextIn: 12, everyDays: 365 },
  { id: "sub_loom", name: "Loom Business", domain: "loom.com", category: "Productivity", interval: "monthly", amounts: [1250, 1250, 1250, 1250, 1250, 1250], descriptor: "LOOM.COM", status: "candidate", confidence: 0.86, explanation: "Monthly cadence. No product emails other than receipts in 6 months.", nextIn: 20, everyDays: 30 },
  { id: "sub_unknown", name: "PAYPAL *DGTLSRV", domain: "", category: "Unknown", interval: "monthly", amounts: [999, 999, 999, 999], descriptor: "PAYPAL *DGTLSRV 4029357733", status: "candidate", confidence: 0.62, explanation: "Recurring PayPal charge with a generic descriptor; no matching email evidence.", nextIn: 5, everyDays: 30 },
  { id: "sub_hetzner", name: "Hetzner Cloud", domain: "hetzner.com", category: "Infrastructure", interval: "monthly", amounts: [1190, 1190, 1190, 1190], currency: "EUR", descriptor: "HETZNER ONLINE GMBH", status: "confirmed", confidence: 0.93, explanation: "Monthly EUR charges, matched to Hetzner invoice emails.", nextIn: 1, everyDays: 30 },
];

let transactions: Transaction[] = [];
let evidence: Record<string, EmailEvidence[]> = {};
let subscriptions: Subscription[] = seeds.map((s) => {
  const cur = s.currency ?? "USD";
  const n = s.amounts.length;
  evidence[s.id] = [];
  s.amounts.forEach((amt, i) => {
    const ago = (n - i) * s.everyDays - (s.nextIn ?? 0) + (i % 2);
    const tx: Transaction = {
      id: `tx_${s.id}_${i}`,
      connectionId: "conn_bank",
      accountName: "Chase Business ••4821",
      postedAt: daysAgo(ago),
      amount: { amountMinor: -amt, currency: cur },
      descriptionRaw: s.descriptor,
      merchantNormalized: s.domain ? s.name : null,
      status: "posted",
      isRecurringCandidate: true,
      subscriptionId: s.id,
    };
    transactions.push(tx);
    if (s.domain && s.id !== "sub_loom") {
      evidence[s.id]!.push({
        id: `ev_${s.id}_${i}`,
        receivedAt: daysAgo(ago + 0.2),
        senderDomain: s.domain,
        subjectMinimized: `Your ${s.name} receipt`,
        evidenceType: s.interval === "annual" ? "renewal" : "receipt",
        amount: { amountMinor: amt, currency: cur },
        invoiceDate: daysAgo(ago),
        extractionConfidence: 0.9,
        matchScore: 0.92,
        matchStatus: i === n - 1 ? "suggested" : "confirmed",
        matchReason: "Vendor domain, exact amount, and date within 1 day.",
      });
    }
  });
  const last = s.amounts[n - 1] ?? 0;
  return {
    id: s.id,
    vendorName: s.name,
    vendorDomain: s.domain || null,
    category: s.category,
    displayName: s.name,
    status: s.status,
    billingInterval: s.interval,
    expectedAmount: { amountMinor: last, currency: cur },
    monthlyEquivalent: { amountMinor: monthlyEquivalentMinor(last, s.interval), currency: cur },
    estimatedNextChargeAt: s.nextIn === null ? null : daysAhead(s.nextIn),
    detectionConfidence: s.confidence,
    detectionExplanation: s.explanation,
    lastDetectedAt: daysAgo(0.1),
    note: null,
  };
});

// one-off noise
[
  ["UBER *TRIP", 2340],
  ["STAPLES 0042", 6712],
  ["DELTA AIR 0062", 41200],
  ["CLIENT PAYMENT - ACME CO", -350000],
  ["STARBUCKS #1182", 645],
].forEach(([d, a], i) =>
  transactions.push({
    id: `tx_misc_${i}`,
    connectionId: "conn_bank",
    accountName: "Chase Business ••4821",
    postedAt: daysAgo(3 + i * 9),
    amount: usd(-(a as number)),
    descriptionRaw: d as string,
    merchantNormalized: null,
    status: i === 0 ? "pending" : "posted",
    isRecurringCandidate: false,
    subscriptionId: null,
  }),
);
transactions.sort((a, b) => b.postedAt.localeCompare(a.postedAt));

let findings: Finding[] = [
  { id: "fnd_dup", subscriptionId: "sub_adobe", subscriptionName: "Adobe Creative Cloud", findingType: "possible_duplicate", severity: "high", status: "new", title: "Two design suites billed in parallel", explanation: "Adobe Creative Cloud and Figma Professional both charge monthly in the Design category. If you only use one, you could cancel the other.", estimatedImpact: usd(5999), confidence: 0.72, ruleVersion: "dup-v1.2", createdAt: daysAgo(2), updatedAt: daysAgo(2) },
  { id: "fnd_price_notion", subscriptionId: "sub_notion", subscriptionName: "Notion Plus", findingType: "price_increase", severity: "medium", status: "new", title: "Notion Plus went up 20%", explanation: "Charged $10.00 for 3 cycles, then $12.00 for the last 3 cycles.", estimatedImpact: usd(200), confidence: 0.95, ruleVersion: "price-v1.0", createdAt: daysAgo(55), updatedAt: daysAgo(55) },
  { id: "fnd_price_adobe", subscriptionId: "sub_adobe", subscriptionName: "Adobe Creative Cloud", findingType: "price_increase", severity: "medium", status: "reviewing", title: "Adobe Creative Cloud went up 9%", explanation: "Charged $54.99 for 3 cycles, then $59.99.", estimatedImpact: usd(500), confidence: 0.95, ruleVersion: "price-v1.0", createdAt: daysAgo(50), updatedAt: daysAgo(10) },
  { id: "fnd_loom", subscriptionId: "sub_loom", subscriptionName: "Loom Business", findingType: "low_evidence", severity: "medium", status: "new", title: "Loom may be forgotten", explanation: "Six monthly charges with no product activity emails — only receipts. We can't see actual usage; review whether you still use it.", estimatedImpact: usd(1250), confidence: 0.55, ruleVersion: "low-ev-v0.9", createdAt: daysAgo(4), updatedAt: daysAgo(4) },
  { id: "fnd_renew", subscriptionId: "sub_domain", subscriptionName: "Namecheap domains", findingType: "renewal_approaching", severity: "low", status: "new", title: "Annual domain renewal in 12 days", explanation: "Last renewal was $34.98. Expected renewal around the same amount.", estimatedImpact: usd(3498), confidence: 0.8, ruleVersion: "renew-v1.0", createdAt: daysAgo(1), updatedAt: daysAgo(1) },
  { id: "fnd_unclear", subscriptionId: "sub_unknown", subscriptionName: "PAYPAL *DGTLSRV", findingType: "unclear_vendor", severity: "high", status: "new", title: "Unidentified recurring PayPal charge", explanation: "A $9.99 monthly charge through PayPal with a generic descriptor. No matching invoice found in Gmail.", estimatedImpact: usd(999), confidence: 0.62, ruleVersion: "unclear-v1.0", createdAt: daysAgo(6), updatedAt: daysAgo(6) },
];
const reviews: Record<string, UserReview[]> = {};

function summary() {
  const active = subscriptions.filter((s) => s.status !== "dismissed" && s.status !== "inactive");
  // Mock FX: EUR→USD 1.08 (real backend should own conversion and expose rates).
  const toUsd = (m: Money) => (m.currency === "EUR" ? Math.round(m.amountMinor * 1.08) : m.amountMinor);
  const monthly = active.reduce((a, s) => a + (s.monthlyEquivalent ? toUsd(s.monthlyEquivalent) : 0), 0);
  const open = findings.filter((f) => ["new", "reviewing"].includes(f.status));
  const cats: Record<string, number> = {};
  active.forEach((s) => (cats[s.category ?? "Other"] = (cats[s.category ?? "Other"] ?? 0) + (s.monthlyEquivalent ? toUsd(s.monthlyEquivalent) : 0)));
  const savings = Object.values(reviews).flat().reduce((a, r) => a + (r.estimatedSavings?.amountMinor ?? 0), 0);
  return {
    monthlyRecurringSpend: usd(monthly),
    annualizedSpend: usd(monthly * 12),
    subscriptionCount: active.length,
    candidateCount: active.filter((s) => s.status === "candidate").length,
    openFindingsCount: open.length,
    potentialSavings: usd(open.filter((f) => f.findingType !== "renewal_approaching").reduce((a, f) => a + (f.estimatedImpact?.amountMinor ?? 0), 0)),
    userEstimatedSavings: usd(savings),
    upcoming: active
      .filter((s) => s.estimatedNextChargeAt)
      .sort((a, b) => a.estimatedNextChargeAt!.localeCompare(b.estimatedNextChargeAt!))
      .slice(0, 5)
      .map((s) => ({ subscriptionId: s.id, name: s.displayName, date: s.estimatedNextChargeAt!, amount: s.expectedAmount })),
    recentChanges: [
      { subscriptionId: "sub_unknown", name: "PAYPAL *DGTLSRV", kind: "new" as const, date: daysAgo(6), detail: "New recurring charge detected" },
      { subscriptionId: "sub_notion", name: "Notion Plus", kind: "price_change" as const, date: daysAgo(55), detail: "$10.00 → $12.00" },
      { subscriptionId: "sub_adobe", name: "Adobe Creative Cloud", kind: "price_change" as const, date: daysAgo(50), detail: "$54.99 → $59.99" },
    ],
    spendByCategory: Object.entries(cats).map(([category, v]) => ({ category, monthly: usd(v) })).sort((a, b) => b.monthly.amountMinor - a.monthly.amountMinor),
    connections: clone(connections),
  };
}

function findingDetail(id: string): FindingDetail {
  const f = findings.find((x) => x.id === id);
  if (!f) throw new Error("Finding not found");
  const txs = transactions.filter((t) => t.subscriptionId === f.subscriptionId).slice(0, 4);
  const evs = (f.subscriptionId && evidence[f.subscriptionId]?.slice(-2)) || [];
  return clone({
    ...f,
    evidence: [
      ...txs.map((t, i) => ({ role: (i === 0 ? "trigger" : "supporting") as "trigger" | "supporting", explanation: i === 0 ? "Most recent charge that triggered this rule." : "Earlier charge in the same series.", transaction: t })),
      ...evs.map((e) => ({ role: "context" as const, explanation: "Matched email evidence.", email: e })),
    ],
    reviews: reviews[id] ?? [],
  });
}

function getSub(id: string) {
  const s = subscriptions.find((x) => x.id === id);
  if (!s) throw new Error("Subscription not found");
  return s;
}

export const mockApi: ApiClient = {
  async createSession(email) {
    await delay();
    return { token: "mock-token", user: { ...user, email } };
  },
  async getMe() { await delay(80); return clone(user); },
  async getWorkspace() { await delay(80); return clone(workspace); },
  async deleteAccount() { await delay(600); },

  async listIntegrations() { await delay(); return clone(connections); },
  async connectBank() {
    await delay(900);
    const c: IntegrationConnection = { id: uid("conn"), kind: "bank", provider: "truelayer", displayName: "Revolut Business ••0193", status: "active", syncState: "initial_sync", scopesGranted: ["transactions:read"], lastSyncAt: null, lastSyncStatus: "running", createdAt: new Date().toISOString() };
    connections.push(c);
    setTimeout(() => Object.assign(c, { syncState: "up_to_date", lastSyncAt: new Date().toISOString(), lastSyncStatus: "success" }), 4000);
    return { redirectUrl: null, connection: clone(c) };
  },
  async connectGmail() {
    await delay(900);
    let c = connections.find((x) => x.kind === "gmail");
    if (c) Object.assign(c, { status: "active", syncState: "up_to_date", lastSyncAt: new Date().toISOString(), lastSyncStatus: "success" });
    else {
      c = { id: uid("conn"), kind: "gmail", provider: "google", displayName: user.email, status: "active", syncState: "up_to_date", scopesGranted: ["gmail.readonly"], lastSyncAt: new Date().toISOString(), lastSyncStatus: "success", createdAt: new Date().toISOString() };
      connections.push(c);
    }
    return { redirectUrl: null, connection: clone(c) };
  },
  async syncIntegration(id) {
    await delay(1200);
    const c = connections.find((x) => x.id === id);
    if (!c) throw new Error("Connection not found");
    if (c.status === "needs_reauth") throw new Error("Reauthorization required");
    Object.assign(c, { syncState: "up_to_date", lastSyncAt: new Date().toISOString(), lastSyncStatus: "success" });
    return clone(c);
  },
  async disconnectIntegration(id, deleteData) {
    await delay();
    connections = connections.filter((c) => c.id !== id);
    if (deleteData) {
      transactions = transactions.filter((t) => t.connectionId !== id);
      if (id === "conn_gmail") evidence = {};
    }
  },

  async getDashboardSummary() { await delay(); return clone(summary()); },
  async listTransactions(q = {}) {
    await delay();
    let items = transactions;
    if (q.recurringOnly) items = items.filter((t) => t.isRecurringCandidate);
    if (q.search) {
      const s = q.search.toLowerCase();
      items = items.filter((t) => t.descriptionRaw.toLowerCase().includes(s) || t.merchantNormalized?.toLowerCase().includes(s));
    }
    const limit = q.limit ?? 50;
    const start = q.cursor ? Number(q.cursor) : 0;
    const page = items.slice(start, start + limit);
    return clone({ items: page, total: items.length, nextCursor: start + limit < items.length ? String(start + limit) : null });
  },
  async listSubscriptions() { await delay(); return clone(subscriptions); },
  async getSubscription(id) {
    await delay();
    const s = getSub(id);
    return clone({
      ...s,
      transactions: transactions.filter((t) => t.subscriptionId === id),
      evidence: evidence[id] ?? [],
      findings: findings.filter((f) => f.subscriptionId === id),
    });
  },
  async listFindings(q = {}) {
    await delay();
    let items = findings;
    if (q.status === "open") items = items.filter((f) => f.status === "new" || f.status === "reviewing");
    else if (q.status) items = items.filter((f) => f.status === q.status);
    if (q.type) items = items.filter((f) => f.findingType === q.type);
    return clone(items);
  },
  async getFinding(id) { await delay(); return findingDetail(id); },

  async reviewFinding(id, input) {
    await delay();
    const f = findings.find((x) => x.id === id);
    if (!f) throw new Error("Finding not found");
    const statusMap = { confirm: "confirmed", dismiss: "dismissed", mark_reviewing: "reviewing", resolve: "resolved" } as const;
    f.status = statusMap[input.decision];
    f.updatedAt = new Date().toISOString();
    (reviews[id] ??= []).unshift({ id: uid("rev"), decision: input.decision, note: input.note ?? null, estimatedSavings: input.estimatedSavings ?? null, createdAt: f.updatedAt });
    return findingDetail(id);
  },
  async updateSubscription(id, patch) {
    await delay();
    const s = getSub(id);
    Object.assign(s, patch);
    if (patch.expectedAmount || patch.billingInterval) {
      const amt = s.expectedAmount;
      s.monthlyEquivalent = amt ? { amountMinor: monthlyEquivalentMinor(amt.amountMinor, s.billingInterval), currency: amt.currency } : null;
    }
    return clone(s);
  },
  async confirmSubscription(id) { await delay(); const s = getSub(id); s.status = "confirmed"; return clone(s); },
  async dismissSubscription(id) { await delay(); const s = getSub(id); s.status = "dismissed"; return clone(s); },
};

void eur;
