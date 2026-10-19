import type {
  DashboardSummary,
  Finding,
  FindingDetail,
  FindingQuery,
  IntegrationConnection,
  Paginated,
  ReviewInput,
  Subscription,
  SubscriptionDetail,
  SubscriptionPatch,
  Transaction,
  TransactionQuery,
  User,
  Workspace,
} from "./types";
import { mockApi } from "./mock";

/**
 * The single contract between the frontend and the backend.
 * Each method maps 1:1 to an endpoint in the spec (section 10).
 * Implement these endpoints in your backend, then set VITE_API_MODE=http and VITE_API_BASE_URL.
 */
export interface ApiClient {
  createSession(email: string, password: string): Promise<{ token: string; user: User }>; // POST /auth/session
  getMe(): Promise<User>; // GET /me
  getWorkspace(): Promise<Workspace>; // GET /workspace
  deleteAccount(): Promise<void>; // DELETE /account

  listIntegrations(): Promise<IntegrationConnection[]>; // GET /integrations
  connectBank(): Promise<{ redirectUrl: string | null; connection: IntegrationConnection }>; // POST /integrations/bank/connect
  connectGmail(): Promise<{ redirectUrl: string | null; connection: IntegrationConnection }>; // POST /integrations/gmail/connect
  syncIntegration(connectionId: string): Promise<IntegrationConnection>; // POST /integrations/{id}/sync
  disconnectIntegration(connectionId: string, deleteData: boolean): Promise<void>; // POST /integrations/{id}/disconnect

  getDashboardSummary(): Promise<DashboardSummary>; // GET /dashboard/summary
  listTransactions(q?: TransactionQuery): Promise<Paginated<Transaction>>; // GET /transactions
  listSubscriptions(): Promise<Subscription[]>; // GET /subscriptions
  getSubscription(id: string): Promise<SubscriptionDetail>; // GET /subscriptions/{id}
  listFindings(q?: FindingQuery): Promise<Finding[]>; // GET /findings
  getFinding(id: string): Promise<FindingDetail>; // GET /findings/{id}

  reviewFinding(id: string, input: ReviewInput): Promise<FindingDetail>; // POST /findings/{id}/review
  updateSubscription(id: string, patch: SubscriptionPatch): Promise<Subscription>; // PATCH /subscriptions/{id}
  confirmSubscription(id: string): Promise<Subscription>; // POST /subscriptions/{id}/confirm
  dismissSubscription(id: string): Promise<Subscription>; // POST /subscriptions/{id}/dismiss
}

const TOKEN_KEY = "tracker.token";
export const tokenStore = {
  get: () => (typeof window === "undefined" ? null : window.localStorage.getItem(TOKEN_KEY)),
  set: (t: string) => window.localStorage.setItem(TOKEN_KEY, t),
  clear: () => window.localStorage.removeItem(TOKEN_KEY),
};

export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
  ) {
    super(message);
  }
}

function createHttpApi(baseUrl: string): ApiClient {
  async function req<T>(method: string, path: string, body?: unknown, query?: Record<string, unknown>): Promise<T> {
    const url = new URL(baseUrl.replace(/\/$/, "") + path);
    if (query) for (const [k, v] of Object.entries(query)) if (v !== undefined && v !== "") url.searchParams.set(k, String(v));
    const token = tokenStore.get();
    const headers: Record<string, string> = { Accept: "application/json" };
    if (body !== undefined) headers["Content-Type"] = "application/json";
    if (token) headers["Authorization"] = `Bearer ${token}`;
    if (method !== "GET") headers["Idempotency-Key"] = crypto.randomUUID();
    const res = await fetch(url, { method, headers, body: body === undefined ? null : JSON.stringify(body) });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new ApiError(res.status, err.code ?? "http_error", err.message ?? res.statusText);
    }
    return res.status === 204 ? (undefined as T) : res.json();
  }
  return {
    createSession: (email, password) => req("POST", "/auth/session", { email, password }),
    getMe: () => req("GET", "/me"),
    getWorkspace: () => req("GET", "/workspace"),
    deleteAccount: () => req("DELETE", "/account"),
    listIntegrations: () => req("GET", "/integrations"),
    connectBank: () => req("POST", "/integrations/bank/connect", {}),
    connectGmail: () => req("POST", "/integrations/gmail/connect", {}),
    syncIntegration: (id) => req("POST", `/integrations/${id}/sync`, {}),
    disconnectIntegration: (id, deleteData) => req("POST", `/integrations/${id}/disconnect`, { deleteData }),
    getDashboardSummary: () => req("GET", "/dashboard/summary"),
    listTransactions: (q) => req("GET", "/transactions", undefined, { ...q }),
    listSubscriptions: () => req("GET", "/subscriptions"),
    getSubscription: (id) => req("GET", `/subscriptions/${id}`),
    listFindings: (q) => req("GET", "/findings", undefined, { ...q }),
    getFinding: (id) => req("GET", `/findings/${id}`),
    reviewFinding: (id, input) => req("POST", `/findings/${id}/review`, input),
    updateSubscription: (id, patch) => req("PATCH", `/subscriptions/${id}`, patch),
    confirmSubscription: (id) => req("POST", `/subscriptions/${id}/confirm`, {}),
    dismissSubscription: (id) => req("POST", `/subscriptions/${id}/dismiss`, {}),
  };
}

const mode = import.meta.env["VITE_API_MODE"] ?? "mock";
export const API_MODE: "mock" | "http" = mode === "http" ? "http" : "mock";

export const api: ApiClient =
  API_MODE === "http" ? createHttpApi(import.meta.env["VITE_API_BASE_URL"] ?? "http://localhost:3000") : mockApi;
