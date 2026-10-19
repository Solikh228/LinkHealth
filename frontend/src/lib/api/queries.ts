import { queryOptions } from "@tanstack/react-query";
import { api } from "./client";
import type { FindingQuery, TransactionQuery } from "./types";

export const qk = {
  all: ["api"] as const,
};

export const dashboardQuery = () => queryOptions({ queryKey: ["api", "dashboard"], queryFn: () => api.getDashboardSummary() });
export const integrationsQuery = () => queryOptions({ queryKey: ["api", "integrations"], queryFn: () => api.listIntegrations() });
export const subscriptionsQuery = () => queryOptions({ queryKey: ["api", "subscriptions"], queryFn: () => api.listSubscriptions() });
export const subscriptionQuery = (id: string) => queryOptions({ queryKey: ["api", "subscriptions", id], queryFn: () => api.getSubscription(id) });
export const findingsQuery = (q: FindingQuery = {}) => queryOptions({ queryKey: ["api", "findings", q], queryFn: () => api.listFindings(q) });
export const findingQuery = (id: string) => queryOptions({ queryKey: ["api", "finding", id], queryFn: () => api.getFinding(id) });
export const transactionsQuery = (q: TransactionQuery = {}) => queryOptions({ queryKey: ["api", "transactions", q], queryFn: () => api.listTransactions(q) });
export const meQuery = () => queryOptions({ queryKey: ["api", "me"], queryFn: () => api.getMe() });
