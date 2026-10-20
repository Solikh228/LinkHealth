import { useState, useEffect, useMemo } from "react";
import { Clock, Filter, AlertCircle } from "lucide-react";
import { toast } from "sonner";
import { PageHeader } from "@/components/app/AppShell";
import { Skeleton } from "@/components/ui/skeleton";
import { RenewalItemCard } from "@/components/renewals/RenewalItemCard";
import { mockService } from "@/services/mockService";
import type { Renewal } from "@/types";

export function RenewalsPage() {
  const [renewals, setRenewals] = useState<Renewal[]>([]);
  const [loading, setLoading] = useState(true);
  const [highSpendOnly, setHighSpendOnly] = useState(false);

  const fetchRenewals = async () => {
    setLoading(true);
    try {
      const data = await mockService.getRenewals();
      setRenewals(data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRenewals();
  }, []);

  const handleToggleReminder = (id: string) => {
    setRenewals((prev) =>
      prev.map((r) => {
        if (r.id === id) {
          const next = !r.hasReminder;
          toast.info(next ? `Priority reminder enabled for ${r.vendorName}` : `Reminder disabled`);
          return { ...r, hasReminder: next };
        }
        return r;
      })
    );
  };

  const filtered = useMemo(() => {
    if (!highSpendOnly) return renewals;
    // High spend threshold: > $50 (5000 minor units)
    return renewals.filter((r) => r.amount.amountMinor >= 5000);
  }, [renewals, highSpendOnly]);

  const next7Days = filtered.filter((r) => r.timeWindow === "next_7_days");
  const next30Days = filtered.filter((r) => r.timeWindow === "next_30_days");
  const laterQuarter = filtered.filter((r) => r.timeWindow === "later_this_quarter");

  return (
    <div className="space-y-8">
      <PageHeader eyebrow="Timeline & Schedule" title="Renewals">
        <div className="flex items-center gap-2 rounded-lg border bg-card p-1">
          <button
            onClick={() => setHighSpendOnly(false)}
            className={`rounded px-3 py-1 text-xs font-medium transition ${
              !highSpendOnly ? "bg-primary text-primary-foreground shadow" : "text-muted-foreground hover:text-foreground"
            }`}
          >
            All Renewals ({renewals.length})
          </button>
          <button
            onClick={() => setHighSpendOnly(true)}
            className={`rounded px-3 py-1 text-xs font-medium transition ${
              highSpendOnly ? "bg-primary text-primary-foreground shadow" : "text-muted-foreground hover:text-foreground"
            }`}
          >
            High-Spend Only (&gt; $50)
          </button>
        </div>
      </PageHeader>

      <p className="-mt-4 text-sm text-muted-foreground max-w-3xl">
        Chronological schedule of expected subscription renewals and auto-charges. Set priority reminders to prevent surprise charges before cancellation deadlines.
      </p>

      {loading ? (
        <div className="space-y-4">
          <Skeleton className="h-24 w-full" />
          <Skeleton className="h-24 w-full" />
          <Skeleton className="h-24 w-full" />
        </div>
      ) : (
        <div className="space-y-8">
          {/* Next 7 Days */}
          <section className="space-y-3">
            <div className="flex items-center gap-2 border-b pb-2">
              <span className="size-2 rounded-full bg-destructive animate-pulse" />
              <h3 className="text-sm font-bold uppercase tracking-wider text-foreground">
                Next 7 Days ({next7Days.length})
              </h3>
            </div>
            {next7Days.length > 0 ? (
              <div className="grid gap-3">
                {next7Days.map((r) => (
                  <RenewalItemCard key={r.id} renewal={r} onToggleReminder={handleToggleReminder} />
                ))}
              </div>
            ) : (
              <p className="text-xs text-muted-foreground py-2">No charges scheduled in the next 7 days.</p>
            )}
          </section>

          {/* Next 30 Days */}
          <section className="space-y-3">
            <div className="flex items-center gap-2 border-b pb-2">
              <span className="size-2 rounded-full bg-amber-500" />
              <h3 className="text-sm font-bold uppercase tracking-wider text-foreground">
                Next 30 Days ({next30Days.length})
              </h3>
            </div>
            {next30Days.length > 0 ? (
              <div className="grid gap-3">
                {next30Days.map((r) => (
                  <RenewalItemCard key={r.id} renewal={r} onToggleReminder={handleToggleReminder} />
                ))}
              </div>
            ) : (
              <p className="text-xs text-muted-foreground py-2">No charges scheduled in the next 30 days.</p>
            )}
          </section>

          {/* Later This Quarter */}
          <section className="space-y-3">
            <div className="flex items-center gap-2 border-b pb-2">
              <span className="size-2 rounded-full bg-muted-foreground" />
              <h3 className="text-sm font-bold uppercase tracking-wider text-foreground">
                Later This Quarter ({laterQuarter.length})
              </h3>
            </div>
            {laterQuarter.length > 0 ? (
              <div className="grid gap-3">
                {laterQuarter.map((r) => (
                  <RenewalItemCard key={r.id} renewal={r} onToggleReminder={handleToggleReminder} />
                ))}
              </div>
            ) : (
              <p className="text-xs text-muted-foreground py-2">No later quarter renewals detected.</p>
            )}
          </section>
        </div>
      )}
    </div>
  );
}
