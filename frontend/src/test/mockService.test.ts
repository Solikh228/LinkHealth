import { describe, it, expect } from "vitest";
import { mockService } from "../services/mockService";

describe("Frontend Mock Service & Synthetic Fixtures", () => {
  it("provides at least 8 realistic business subscriptions", async () => {
    const subs = await mockService.getSubscriptions();
    expect(subs.length).toBeGreaterThanOrEqual(8);
    const names = subs.map((s) => s.name);
    expect(names).toContain("Amazon Web Services");
    expect(names).toContain("Figma Professional");
    expect(names).toContain("Adobe Creative Cloud");
  });

  it("includes all required finding types", async () => {
    const findings = await mockService.getFindings();
    const types = new Set(findings.map((f) => f.type));
    expect(types.has("forgotten_charge")).toBe(true);
    expect(types.has("trial_conversion")).toBe(true);
    expect(types.has("price_increase")).toBe(true);
    expect(types.has("duplicate_service")).toBe(true);
    expect(types.has("renewal_approaching")).toBe(true);
  });

  it("updates finding decision and adjusts confirmed savings", async () => {
    const updated = await mockService.updateFindingDecision("fnd_forgotten", "confirmed_waste", "No longer needed");
    expect(updated.status).toBe("confirmed_waste");
    expect(updated.confirmedSavings?.amountMinor).toBe(1599);

    const metrics = await mockService.getOverviewMetrics();
    expect(metrics.confirmedSavings.amountMinor).toBeGreaterThanOrEqual(1599);
  });

  it("triggers sync and disconnects connections", async () => {
    const synced = await mockService.triggerSync("conn_bank_1");
    expect(synced.status).toBe("connected");
    await mockService.disconnectConnection("conn_bank_1");
    const connections = await mockService.getConnections();
    expect(connections.find((c) => c.id === "conn_bank_1")).toBeUndefined();
  });
});
