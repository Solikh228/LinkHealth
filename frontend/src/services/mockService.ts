import type {
  BillingEvidence,
  Connection,
  Finding,
  FindingDecision,
  OverviewMetrics,
  Subscription,
  Transaction,
} from "../types";

const delay = (min = 200, max = 350) =>
  new Promise((resolve) => setTimeout(resolve, Math.floor(Math.random() * (max - min + 1)) + min));

// 8 realistic business subscriptions
let subscriptions: Subscription[] = [
  {
    id: "sub_aws",
    name: "Amazon Web Services",
    vendorDomain: "aws.amazon.com",
    category: "Infrastructure",
    status: "active",
    billingInterval: "monthly",
    amount: { amountMinor: 4900, currency: "USD" },
    monthlyEquivalent: { amountMinor: 4900, currency: "USD" },
    nextRenewalDate: "2026-11-02",
    confidence: 0.95,
    explanation: "Consistent monthly cloud hosting infrastructure usage.",
    lastChargeDate: "2026-10-02",
  },
  {
    id: "sub_github",
    name: "GitHub Team",
    vendorDomain: "github.com",
    category: "Engineering",
    status: "active",
    billingInterval: "monthly",
    amount: { amountMinor: 2100, currency: "USD" },
    monthlyEquivalent: { amountMinor: 2100, currency: "USD" },
    nextRenewalDate: "2026-11-05",
    confidence: 0.98,
    explanation: "Monthly software version control and CI/CD seats.",
    lastChargeDate: "2026-10-05",
  },
  {
    id: "sub_figma",
    name: "Figma Professional",
    vendorDomain: "figma.com",
    category: "Design",
    status: "active",
    billingInterval: "monthly",
    amount: { amountMinor: 1500, currency: "USD" },
    monthlyEquivalent: { amountMinor: 1500, currency: "USD" },
    nextRenewalDate: "2026-10-27",
    confidence: 0.97,
    explanation: "Monthly design collaboration tool billed consistently.",
    lastChargeDate: "2026-09-27",
  },
  {
    id: "sub_google",
    name: "Google Workspace",
    vendorDomain: "google.com",
    category: "Productivity",
    status: "active",
    billingInterval: "monthly",
    amount: { amountMinor: 1800, currency: "USD" },
    monthlyEquivalent: { amountMinor: 1800, currency: "USD" },
    nextRenewalDate: "2026-11-01",
    confidence: 0.99,
    explanation: "Business email and cloud productivity suite.",
    lastChargeDate: "2026-10-01",
  },
  {
    id: "sub_zoom",
    name: "Zoom Workplace",
    vendorDomain: "zoom.us",
    category: "Communication",
    status: "active",
    billingInterval: "monthly",
    amount: { amountMinor: 1599, currency: "USD" },
    monthlyEquivalent: { amountMinor: 1599, currency: "USD" },
    nextRenewalDate: "2026-10-25",
    confidence: 0.89,
    explanation: "Video conferencing pro license with low recent activity.",
    lastChargeDate: "2026-09-25",
  },
  {
    id: "sub_adobe",
    name: "Adobe Creative Cloud",
    vendorDomain: "adobe.com",
    category: "Design",
    status: "candidate",
    billingInterval: "monthly",
    amount: { amountMinor: 5999, currency: "USD" },
    monthlyEquivalent: { amountMinor: 5999, currency: "USD" },
    nextRenewalDate: "2026-10-30",
    confidence: 0.94,
    explanation: "Design suite overlapping with Figma Professional.",
    lastChargeDate: "2026-09-30",
  },
  {
    id: "sub_notion",
    name: "Notion Plus",
    vendorDomain: "notion.so",
    category: "Productivity",
    status: "active",
    billingInterval: "monthly",
    amount: { amountMinor: 1200, currency: "USD" },
    monthlyEquivalent: { amountMinor: 1200, currency: "USD" },
    nextRenewalDate: "2026-10-22",
    confidence: 0.91,
    explanation: "Monthly knowledge base, recent price increase from $10 to $12.",
    lastChargeDate: "2026-09-22",
  },
  {
    id: "sub_slack",
    name: "Slack Pro",
    vendorDomain: "slack.com",
    category: "Communication",
    status: "active",
    billingInterval: "annual",
    amount: { amountMinor: 10400, currency: "USD" },
    monthlyEquivalent: { amountMinor: 867, currency: "USD" },
    nextRenewalDate: "2026-10-31",
    confidence: 0.93,
    explanation: "Team communication annual plan renewal approaching.",
    lastChargeDate: "2025-10-31",
  },
];

// Evidence items
const evidenceMap: Record<string, BillingEvidence[]> = {
  sub_zoom: [
    {
      id: "ev_zoom_1",
      subscriptionId: "sub_zoom",
      senderDomain: "zoom.us",
      subject: "Your Zoom Invoice #INV-88219",
      receivedAt: "2026-09-25T10:00:00Z",
      snippet: "Payment received for Zoom Workplace Pro. No host activity recorded in 90 days.",
      extractedAmountMinor: 1599,
      confidence: 0.92,
    },
  ],
  sub_adobe: [
    {
      id: "ev_adobe_1",
      subscriptionId: "sub_adobe",
      senderDomain: "adobe.com",
      subject: "Adobe Subscription Renewal Notice",
      receivedAt: "2026-09-30T09:15:00Z",
      snippet: "Creative Cloud All Apps subscription billed at $59.99/mo.",
      extractedAmountMinor: 5999,
      confidence: 0.95,
    },
  ],
  sub_notion: [
    {
      id: "ev_notion_1",
      subscriptionId: "sub_notion",
      senderDomain: "notion.so",
      subject: "Upcoming plan price update",
      receivedAt: "2026-08-15T14:20:00Z",
      snippet: "Your workspace Notion Plus subscription rate increased from $10.00 to $12.00 per month.",
      extractedAmountMinor: 1200,
      confidence: 0.96,
    },
  ],
  sub_slack: [
    {
      id: "ev_slack_1",
      subscriptionId: "sub_slack",
      senderDomain: "slack.com",
      subject: "Annual Renewal Notice: Slack Pro",
      receivedAt: "2026-10-15T08:00:00Z",
      snippet: "Your Slack Pro subscription renews on October 31, 2026 for $104.00.",
      extractedAmountMinor: 10400,
      confidence: 0.98,
    },
  ],
};

// All finding types: forgotten recurring charges, trial conversion, price increase, duplicate services, renewal approaching
let findings: Finding[] = [
  {
    id: "fnd_forgotten",
    subscriptionId: "sub_zoom",
    subscriptionName: "Zoom Workplace",
    type: "forgotten_charge",
    severity: "medium",
    status: "open",
    title: "Zoom license may be forgotten",
    explanation: "Monthly charges continue but zero meeting activity has occurred in 90 days.",
    potentialSavings: { amountMinor: 1599, currency: "USD" },
    evidence: evidenceMap["sub_zoom"] || [],
    createdAt: "2026-10-18T10:00:00Z",
  },
  {
    id: "fnd_trial",
    subscriptionId: "sub_notion",
    subscriptionName: "Notion AI Add-on",
    type: "trial_conversion",
    severity: "high",
    status: "open",
    title: "Free trial converted to auto-billing",
    explanation: "30-day trial ended and converted into a recurring $10.00/month charge without explicit confirmation.",
    potentialSavings: { amountMinor: 1000, currency: "USD" },
    evidence: [],
    createdAt: "2026-10-17T11:30:00Z",
  },
  {
    id: "fnd_price",
    subscriptionId: "sub_notion",
    subscriptionName: "Notion Plus",
    type: "price_increase",
    severity: "medium",
    status: "open",
    title: "Notion Plus increased by 20%",
    explanation: "Subscription increased from $10.00/mo to $12.00/mo 3 billing cycles ago.",
    potentialSavings: { amountMinor: 200, currency: "USD" },
    evidence: evidenceMap["sub_notion"] || [],
    createdAt: "2026-10-16T12:00:00Z",
  },
  {
    id: "fnd_duplicate",
    subscriptionId: "sub_adobe",
    subscriptionName: "Adobe Creative Cloud",
    type: "duplicate_service",
    severity: "high",
    status: "open",
    title: "Duplicate design suites billed concurrently",
    explanation: "Adobe Creative Cloud ($59.99/mo) and Figma Professional ($15.00/mo) are both billed monthly for design work.",
    potentialSavings: { amountMinor: 5999, currency: "USD" },
    evidence: evidenceMap["sub_adobe"] || [],
    createdAt: "2026-10-15T09:00:00Z",
  },
  {
    id: "fnd_renewal",
    subscriptionId: "sub_slack",
    subscriptionName: "Slack Pro",
    type: "renewal_approaching",
    severity: "low",
    status: "open",
    title: "Annual renewal approaching in 11 days",
    explanation: "Annual subscription for $104.00 renews automatically on October 31, 2026.",
    potentialSavings: { amountMinor: 10400, currency: "USD" },
    evidence: evidenceMap["sub_slack"] || [],
    createdAt: "2026-10-19T08:00:00Z",
  },
];

let connections: Connection[] = [
  {
    id: "conn_bank_1",
    name: "Chase Business Checking",
    type: "bank",
    provider: "plaid",
    status: "connected",
    lastSyncedAt: "2026-10-20T05:00:00Z",
    accountMask: "••••4821",
  },
  {
    id: "conn_email_1",
    name: "Google Workspace Email",
    type: "email",
    provider: "google",
    status: "connected",
    lastSyncedAt: "2026-10-20T05:00:00Z",
    emailAddress: "alex@studio.dev",
  },
];

let transactions: Transaction[] = [
  {
    id: "tx_1",
    subscriptionId: "sub_figma",
    connectionId: "conn_bank_1",
    accountName: "Chase Business Checking",
    date: "2026-09-27",
    descriptionRaw: "FIGMA.COM *INV48201",
    merchantNormalized: "Figma",
    amount: { amountMinor: -1500, currency: "USD" },
    status: "posted",
    isRecurringCandidate: true,
  },
  {
    id: "tx_2",
    subscriptionId: "sub_adobe",
    connectionId: "conn_bank_1",
    accountName: "Chase Business Checking",
    date: "2026-09-30",
    descriptionRaw: "ADOBE *CREATIVE CLOUD",
    merchantNormalized: "Adobe",
    amount: { amountMinor: -5999, currency: "USD" },
    status: "posted",
    isRecurringCandidate: true,
  },
  {
    id: "tx_3",
    subscriptionId: "sub_aws",
    connectionId: "conn_bank_1",
    accountName: "Chase Business Checking",
    date: "2026-10-02",
    descriptionRaw: "AMAZON WEB SERVICES AWS.AMAZON.CO",
    merchantNormalized: "Amazon Web Services",
    amount: { amountMinor: -4900, currency: "USD" },
    status: "posted",
    isRecurringCandidate: true,
  },
];

export const mockService = {
  async getOverviewMetrics(): Promise<OverviewMetrics> {
    await delay();
    const active = subscriptions.filter((s) => s.status !== "dismissed" && s.status !== "cancelled");
    const monthlySpend = active.reduce((sum, s) => sum + s.monthlyEquivalent.amountMinor, 0);
    const openFindings = findings.filter((f) => f.status === "open");
    const potential = openFindings.reduce((sum, f) => sum + f.potentialSavings.amountMinor, 0);
    const confirmed = findings
      .filter((f) => f.status === "confirmed_waste")
      .reduce((sum, f) => sum + (f.confirmedSavings?.amountMinor ?? f.potentialSavings.amountMinor), 0);

    return {
      monthlyRecurringSpend: { amountMinor: monthlySpend, currency: "USD" },
      annualizedSpend: { amountMinor: monthlySpend * 12, currency: "USD" },
      activeSubscriptionCount: active.length,
      potentialSavings: { amountMinor: potential, currency: "USD" },
      confirmedSavings: { amountMinor: confirmed, currency: "USD" },
      openFindingsCount: openFindings.length,
      upcomingRenewalsCount: active.filter((s) => s.billingInterval === "annual").length,
    };
  },

  async getSubscriptions(): Promise<Subscription[]> {
    await delay();
    return [...subscriptions];
  },

  async getSubscriptionById(id: string): Promise<Subscription | null> {
    await delay();
    const sub = subscriptions.find((s) => s.id === id);
    return sub ? { ...sub } : null;
  },

  async getFindings(): Promise<Finding[]> {
    await delay();
    return [...findings];
  },

  async updateFindingDecision(
    findingId: string,
    decision: FindingDecision,
    note?: string,
  ): Promise<Finding> {
    await delay();
    const f = findings.find((x) => x.id === findingId);
    if (!f) throw new Error(`Finding ${findingId} not found`);

    f.status = decision;
    f.decision = decision;
    f.decisionNote = note;
    f.decisionAt = new Date().toISOString();

    if (decision === "confirmed_waste") {
      f.confirmedSavings = { ...f.potentialSavings };
    }

    return { ...f };
  },

  async getTransactions(): Promise<Transaction[]> {
    await delay();
    return [...transactions];
  },

  async getConnections(): Promise<Connection[]> {
    await delay();
    return [...connections];
  },

  async triggerSync(connectionId: string): Promise<Connection> {
    await delay();
    const c = connections.find((conn) => conn.id === connectionId);
    if (!c) throw new Error(`Connection ${connectionId} not found`);
    c.status = "connected";
    c.lastSyncedAt = new Date().toISOString();
    return { ...c };
  },

  async disconnectConnection(connectionId: string): Promise<void> {
    await delay();
    connections = connections.filter((c) => c.id !== connectionId);
  },

  async deleteUserData(): Promise<void> {
    await delay();
    subscriptions = [];
    findings = [];
    transactions = [];
    connections = [];
  },
};
