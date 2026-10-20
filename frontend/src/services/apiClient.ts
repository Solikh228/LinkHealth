import { toast } from "sonner";
import type {
  Connection,
  Finding,
  FindingDecision,
  OverviewMetrics,
  Renewal,
  Subscription,
  Transaction,
} from "../types";

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${BASE_URL}${endpoint}`;
  try {
    const res = await fetch(url, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
    });

    if (!res.ok) {
      let detail = `Error ${res.status}: ${res.statusText}`;
      try {
        const body = await res.json();
        if (body.detail) {
          detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
        } else if (body.message) {
          detail = body.message;
        }
      } catch {
        // use status text fallback
      }
      toast.error(detail);
      throw new Error(detail);
    }

    if (res.status === 204) {
      return {} as T;
    }
    return (await res.json()) as T;
  } catch (err: any) {
    if (err.name === "TypeError" && err.message?.toLowerCase().includes("fetch")) {
      const msg = "Network error: Unable to connect to server";
      toast.error(msg);
      throw new Error(msg);
    }
    throw err;
  }
}

export const apiClient = {
  async getOverviewMetrics(): Promise<OverviewMetrics> {
    return request<OverviewMetrics>("/api/overview");
  },

  async getSubscriptions(params?: {
    status?: string;
    cadence?: string;
    search?: string;
    skip?: number;
    limit?: number;
  }): Promise<Subscription[]> {
    const query = new URLSearchParams();
    if (params?.status) query.set("status", params.status);
    if (params?.cadence) query.set("cadence", params.cadence);
    if (params?.search) query.set("search", params.search);
    if (params?.skip !== undefined) query.set("skip", params.skip.toString());
    if (params?.limit !== undefined) query.set("limit", params.limit.toString());
    const qs = query.toString();
    return request<Subscription[]>(`/api/subscriptions${qs ? `?${qs}` : ""}`);
  },

  async getSubscriptionById(id: string): Promise<Subscription | null> {
    try {
      return await request<Subscription>(`/api/subscriptions/${id}`);
    } catch {
      return null;
    }
  },

  async patchSubscription(
    id: string,
    payload: {
      name?: string;
      billingInterval?: string;
      category?: string;
      status?: string;
      note?: string;
    },
  ): Promise<Subscription> {
    return request<Subscription>(`/api/subscriptions/${id}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
  },

  async getFindings(params?: {
    status?: string;
    user_decision?: string;
    type?: string;
  }): Promise<Finding[]> {
    const query = new URLSearchParams();
    if (params?.status) query.set("status", params.status);
    if (params?.user_decision) query.set("user_decision", params.user_decision);
    if (params?.type) query.set("type", params.type);
    const qs = query.toString();
    const data = await request<any[]>(`/api/findings${qs ? `?${qs}` : ""}`);
    return data.map((f) => ({
      ...f,
      evidence: f.evidence || [],
    }));
  },

  async updateFindingDecision(
    findingId: string,
    decision: FindingDecision,
    note?: string,
  ): Promise<Finding> {
    const res = await request<Finding>(`/api/findings/${findingId}/action`, {
      method: "POST",
      body: JSON.stringify({ decision, note }),
    });
    return {
      ...res,
      evidence: res.evidence || [],
    };
  },

  async getTransactions(params?: {
    subscriptionId?: string;
    connectionId?: string;
  }): Promise<Transaction[]> {
    const query = new URLSearchParams();
    if (params?.subscriptionId) query.set("subscription_id", params.subscriptionId);
    if (params?.connectionId) query.set("connection_id", params.connectionId);
    const qs = query.toString();
    return request<Transaction[]>(`/api/transactions${qs ? `?${qs}` : ""}`);
  },

  async getConnections(): Promise<Connection[]> {
    return request<Connection[]>("/api/connections");
  },

  async triggerSync(connectionId?: string): Promise<Connection> {
    await request<{ status: string; syncedAt: string }>("/api/connections/sync", {
      method: "POST",
      body: JSON.stringify({ connectionId }),
    });
    const conns = await this.getConnections();
    const matched = connectionId ? conns.find((c) => c.id === connectionId) : conns[0];
    return (
      matched || {
        id: connectionId || "conn_default",
        name: "Synced Connection",
        type: "bank",
        provider: "plaid",
        status: "connected",
        lastSyncedAt: new Date().toISOString(),
      }
    );
  },

  async disconnectConnection(connectionId: string, deleteData = false): Promise<void> {
    await request<{ success: boolean }>(`/api/connections/${connectionId}/disconnect`, {
      method: "POST",
      body: JSON.stringify({ deleteData }),
    });
  },

  async deleteUserData(): Promise<void> {
    await request<void>("/api/user/data", {
      method: "DELETE",
    });
  },

  async getRenewals(): Promise<Renewal[]> {
    const subs = await this.getSubscriptions();
    const now = new Date("2026-10-20");

    const renewals: Renewal[] = subs
      .filter((s) => s.status !== "dismissed" && s.status !== "cancelled" && s.nextRenewalDate)
      .map((s) => {
        const renDate = new Date(s.nextRenewalDate!);
        const diffDays = Math.ceil((renDate.getTime() - now.getTime()) / (1000 * 3600 * 24));

        let timeWindow: "next_7_days" | "next_30_days" | "later_this_quarter" = "later_this_quarter";
        if (diffDays <= 7) {
          timeWindow = "next_7_days";
        } else if (diffDays <= 30) {
          timeWindow = "next_30_days";
        }

        return {
          id: `ren_${s.id}`,
          subscriptionId: s.id,
          vendorName: s.name,
          amount: s.amount,
          dueDate: s.nextRenewalDate!,
          cadence: s.billingInterval,
          evidenceTag: "Detected from recurring transactions",
          hasReminder: s.amount.amountMinor > 5000,
          timeWindow,
        };
      });

    return renewals;
  },

  async toggleRenewalReminder(renewalId: string): Promise<boolean> {
    return true;
  },

  async importCsvStatement(payload: {
    csvContent: string;
    dateColumn?: string;
    merchantColumn?: string;
    amountColumn?: string;
    currencyColumn?: string;
    defaultCurrency?: string;
  }): Promise<{ success: boolean; importedTransactions: number; detectedSubscriptions: number; detectedFindings: number }> {
    return request("/api/statements/import-csv", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async uploadCsvStatement(formData: FormData): Promise<any> {
    const url = `${BASE_URL}/api/statements/upload-csv`;
    const res = await fetch(url, {
      method: "POST",
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "CSV upload failed" }));
      toast.error(err.detail || "CSV upload failed");
      throw new Error(err.detail || "CSV upload failed");
    }
    return res.json();
  },

  getSavingsCsvExportUrl(): string {
    return `${BASE_URL}/api/reports/savings-csv`;
  },
};
