import { useState, useEffect } from "react";
import { Sparkles, CheckCircle2, RefreshCw } from "lucide-react";
import { toast } from "sonner";
import { PageHeader } from "@/components/app/AppShell";
import { Skeleton } from "@/components/ui/skeleton";
import { apiClient } from "@/services/apiClient";
import { WasteCard } from "@/components/waste/WasteCard";
import type { Finding, FindingDecision } from "@/types";

export function WasteFinderPage() {
  const [findings, setFindings] = useState<Finding[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<"open" | "confirmed_waste" | "dismissed">("open");

  const loadFindings = async () => {
    setLoading(true);
    try {
      const data = await apiClient.getFindings();
      setFindings(data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadFindings();
  }, []);

  const handleAction = async (findingId: string, decision: FindingDecision) => {
    const original = findings.find((f) => f.id === findingId);
    if (!original) return;

    // Optimistic UI update
    setFindings((prev) =>
      prev.map((f) => (f.id === findingId ? { ...f, status: decision, decision } : f))
    );

    try {
      await apiClient.updateFindingDecision(findingId, decision);
      toast.success(`Action applied: ${decision.replace("_", " ")}`, {
        description: `Updated status for ${original.subscriptionName}`,
        action: {
          label: "Undo",
          onClick: async () => {
            await apiClient.updateFindingDecision(findingId, "open" as any);
            setFindings((prev) =>
              prev.map((f) => (f.id === findingId ? { ...f, status: "open", decision: undefined } : f))
            );
            toast.info("Action undone");
          },
        },
      });
    } catch {
      toast.error("Failed to update finding decision");
      await loadFindings();
    }
  };

  const displayedFindings = findings.filter((f) => {
    if (filter === "open") return f.status === "open";
    if (filter === "confirmed_waste") return f.status === "confirmed_waste";
    return f.status === "dismissed" || f.status === "snoozed" || f.status === "marked_useful";
  });

  const confirmedSavingsTotal = findings
    .filter((f) => f.status === "confirmed_waste")
    .reduce((sum, f) => sum + (f.confirmedSavings?.amountMinor ?? f.potentialSavings.amountMinor), 0);

  const pendingWasteCount = findings.filter((f) => f.status === "open").length;

  return (
    <div className="space-y-6">
      <PageHeader eyebrow="Hypothesis Engine" title="Waste Finder">
        {confirmedSavingsTotal > 0 && (
          <div className="flex items-center gap-2 rounded-lg border bg-emerald-500/10 px-3 py-1.5 text-xs font-medium text-emerald-600 dark:text-emerald-400">
            <CheckCircle2 className="size-4" />
            <span>Confirmed Savings: ${(confirmedSavingsTotal / 100).toFixed(2)}/mo</span>
          </div>
        )}
      </PageHeader>

      <p className="-mt-4 text-sm text-muted-foreground max-w-3xl">
        Automated hypotheses detecting potential waste: duplicate tools, trial conversions, price increases, and renewals.
        Review each item and confirm whether to keep or cancel.
      </p>

      {/* Filter Tabs */}
      <div className="flex rounded-md border bg-card p-1 max-w-md">
        <button
          onClick={() => setFilter("open")}
          className={`flex-1 rounded px-3 py-1.5 text-xs font-medium transition ${
            filter === "open" ? "bg-primary text-primary-foreground shadow" : "text-muted-foreground hover:text-foreground"
          }`}
        >
          Pending Review ({pendingWasteCount})
        </button>
        <button
          onClick={() => setFilter("confirmed_waste")}
          className={`flex-1 rounded px-3 py-1.5 text-xs font-medium transition ${
            filter === "confirmed_waste" ? "bg-primary text-primary-foreground shadow" : "text-muted-foreground hover:text-foreground"
          }`}
        >
          Confirmed Waste
        </button>
        <button
          onClick={() => setFilter("dismissed")}
          className={`flex-1 rounded px-3 py-1.5 text-xs font-medium transition ${
            filter === "dismissed" ? "bg-primary text-primary-foreground shadow" : "text-muted-foreground hover:text-foreground"
          }`}
        >
          Dismissed / Kept
        </button>
      </div>

      {loading ? (
        <div className="grid gap-6 md:grid-cols-2">
          <Skeleton className="h-72 rounded-lg" />
          <Skeleton className="h-72 rounded-lg" />
          <Skeleton className="h-72 rounded-lg" />
          <Skeleton className="h-72 rounded-lg" />
        </div>
      ) : displayedFindings.length > 0 ? (
        <div className="grid gap-6 md:grid-cols-2">
          {displayedFindings.map((finding) => (
            <WasteCard key={finding.id} finding={finding} onAction={handleAction} />
          ))}
        </div>
      ) : filter === "open" ? (
        /* Zero-Waste Celebration Banner */
        <div className="flex flex-col items-center justify-center rounded-xl border border-emerald-500/30 bg-emerald-500/5 p-12 text-center">
          <div className="rounded-full bg-emerald-500/10 p-4 text-emerald-600 dark:text-emerald-400 mb-4">
            <Sparkles className="size-8" />
          </div>
          <h3 className="font-display text-2xl font-bold text-foreground">Zero Pending Waste Findings!</h3>
          <p className="mt-2 text-sm text-muted-foreground max-w-md">
            You've reviewed all automated subscription hypotheses. We'll alert you the moment a new charge, price hike, or renewal arrives.
          </p>
        </div>
      ) : (
        <div className="rounded-lg border p-12 text-center text-sm text-muted-foreground">
          No findings in this category.
        </div>
      )}
    </div>
  );
}
