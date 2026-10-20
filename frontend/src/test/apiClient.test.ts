import { describe, it, expect, vi, beforeEach } from "vitest";
import { apiClient } from "../services/apiClient";
import { toast } from "sonner";

vi.mock("sonner", () => ({
  toast: {
    error: vi.fn(),
    success: vi.fn(),
    info: vi.fn(),
  },
}));

describe("apiClient", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch = vi.fn();
  });

  it("fetches overview metrics successfully", async () => {
    const mockOverview = {
      monthlyRecurringSpend: { amountMinor: 10000, currency: "USD" },
      annualizedSpend: { amountMinor: 120000, currency: "USD" },
      activeSubscriptionCount: 5,
      potentialSavings: { amountMinor: 2000, currency: "USD" },
      confirmedSavings: { amountMinor: 500, currency: "USD" },
      openFindingsCount: 3,
      upcomingRenewalsCount: 2,
    };

    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => mockOverview,
    });

    const res = await apiClient.getOverviewMetrics();
    expect(res.activeSubscriptionCount).toBe(5);
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/overview"),
      expect.objectContaining({ headers: expect.any(Object) })
    );
  });

  it("sends action request to update finding decision", async () => {
    const mockFinding = {
      id: "fnd_1",
      subscriptionId: "sub_1",
      subscriptionName: "Test Tool",
      type: "forgotten_charge",
      severity: "high",
      status: "confirmed_waste",
      title: "Inactive tool",
      explanation: "No active users",
      potentialSavings: { amountMinor: 4900, currency: "USD" },
      createdAt: "2026-10-20T00:00:00Z",
    };

    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => mockFinding,
    });

    const res = await apiClient.updateFindingDecision("fnd_1", "confirmed_waste", "decommissioned");
    expect(res.status).toBe("confirmed_waste");
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/findings/fnd_1/action"),
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ decision: "confirmed_waste", note: "decommissioned" }),
      })
    );
  });

  it("triggers error toast on 404 or 500 status code", async () => {
    (global.fetch as any).mockResolvedValueOnce({
      ok: false,
      status: 404,
      statusText: "Not Found",
      json: async () => ({ detail: "Subscription not found" }),
    });

    await expect(apiClient.getSubscriptionById("sub_invalid")).resolves.toBeNull();
    expect(toast.error).toHaveBeenCalledWith("Subscription not found");
  });

  it("triggers connection sync and deletes user data cleanly", async () => {
    (global.fetch as any)
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({ status: "synced", syncedAt: "2026-10-20T12:00:00Z" }),
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => [
          {
            id: "conn_1",
            name: "Bank",
            type: "bank",
            provider: "plaid",
            status: "connected",
            lastSyncedAt: "2026-10-20T12:00:00Z",
          },
        ],
      });

    const conn = await apiClient.triggerSync("conn_1");
    expect(conn.status).toBe("connected");

    // Delete user data (204 No Content)
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      status: 204,
      json: async () => ({}),
    });

    await expect(apiClient.deleteUserData()).resolves.toBeUndefined();
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/user/data"),
      expect.objectContaining({ method: "DELETE" })
    );
  });
});
