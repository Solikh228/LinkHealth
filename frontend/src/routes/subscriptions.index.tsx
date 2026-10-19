import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { AppShell, PageHeader } from "@/components/app/AppShell";
import { Confidence, ErrorBox, Loading, SubStatus, intervalLabel } from "@/components/app/bits";
import { subscriptionsQuery } from "@/lib/api/queries";
import type { SubscriptionStatus } from "@/lib/api/types";
import { formatDate, formatMoney } from "@/lib/money";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/subscriptions/")({
  head: () => ({
    meta: [
      { title: "Subscriptions — Ledgerline" },
      { name: "description", content: "Every recurring charge detected across your bank and email." },
      { property: "og:title", content: "Subscriptions — Ledgerline" },
      { property: "og:description", content: "Every recurring charge detected across your bank and email." },
    ],
  }),
  component: Subs,
});

const filters: (SubscriptionStatus | "all")[] = ["all", "candidate", "confirmed", "dismissed"];

function Subs() {
  const { data, isLoading, error } = useQuery(subscriptionsQuery());
  const [f, setF] = useState<(typeof filters)[number]>("all");
  const rows = data?.filter((s) => f === "all" || s.status === f) ?? [];
  return (
    <AppShell>
      <PageHeader eyebrow="Detected" title="Subscriptions">
        <div className="flex rounded-md border bg-card p-0.5">
          {filters.map((x) => (
            <button key={x} onClick={() => setF(x)} className={cn("rounded px-3 py-1 text-sm capitalize", f === x ? "bg-ink text-ink-foreground" : "text-muted-foreground hover:text-foreground")}>
              {x === "candidate" ? "To review" : x}
            </button>
          ))}
        </div>
      </PageHeader>
      {error && <ErrorBox error={error} />}
      {isLoading ? <Loading /> : (
        <div className="overflow-x-auto rounded-lg border bg-card">
          <table className="w-full text-sm">
            <thead className="border-b text-left text-xs uppercase tracking-wider text-muted-foreground">
              <tr><th className="px-5 py-3 font-medium">Vendor</th><th className="px-3 font-medium">Interval</th><th className="px-3 text-right font-medium">Amount</th><th className="px-3 text-right font-medium">/ month</th><th className="px-3 font-medium">Next charge</th><th className="px-3 font-medium">Confidence</th><th className="px-5 font-medium">Status</th></tr>
            </thead>
            <tbody className="divide-y">
              {rows.map((s) => (
                <tr key={s.id} className="hover:bg-muted/40">
                  <td className="px-5 py-3">
                    <Link to="/subscriptions/$id" params={{ id: s.id }} className="font-medium hover:underline">{s.displayName}</Link>
                    <div className="text-xs text-muted-foreground">{s.category} {s.vendorDomain && `· ${s.vendorDomain}`}</div>
                  </td>
                  <td className="px-3">{intervalLabel[s.billingInterval]}</td>
                  <td className="tabular px-3 text-right">{formatMoney(s.expectedAmount)}</td>
                  <td className="tabular px-3 text-right text-muted-foreground">{formatMoney(s.monthlyEquivalent)}</td>
                  <td className="px-3 text-muted-foreground">~{formatDate(s.estimatedNextChargeAt, { month: "short", day: "numeric" })}</td>
                  <td className="px-3"><Confidence v={s.detectionConfidence} /></td>
                  <td className="px-5"><SubStatus s={s.status} /></td>
                </tr>
              ))}
              {rows.length === 0 && <tr><td colSpan={7} className="px-5 py-10 text-center text-muted-foreground">No subscriptions in this view.</td></tr>}
            </tbody>
          </table>
        </div>
      )}
    </AppShell>
  );
}
