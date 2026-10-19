import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { AppShell, PageHeader } from "@/components/app/AppShell";
import { Confidence, ErrorBox, FindingStatusPill, Loading, SeverityDot, findingTypeLabel } from "@/components/app/bits";
import { findingsQuery } from "@/lib/api/queries";
import type { FindingQuery } from "@/lib/api/types";
import { formatDate, formatMoney } from "@/lib/money";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/findings/")({
  head: () => ({
    meta: [
      { title: "Findings — Ledgerline" },
      { name: "description", content: "Evidence-backed potential waste: duplicates, price increases, forgotten tools." },
      { property: "og:title", content: "Findings — Ledgerline" },
      { property: "og:description", content: "Evidence-backed potential waste in your recurring spend." },
    ],
  }),
  component: Findings,
});

const tabs: { k: FindingQuery["status"]; l: string }[] = [
  { k: "open", l: "Open" },
  { k: "confirmed", l: "Confirmed" },
  { k: "resolved", l: "Resolved" },
  { k: "dismissed", l: "Dismissed" },
];

function Findings() {
  const [status, setStatus] = useState<FindingQuery["status"]>("open");
  const { data, isLoading, error } = useQuery(findingsQuery({ status }));
  return (
    <AppShell>
      <PageHeader eyebrow="Potential waste" title="Findings">
        <div className="flex rounded-md border bg-card p-0.5">
          {tabs.map((t) => (
            <button key={t.k} onClick={() => setStatus(t.k)} className={cn("rounded px-3 py-1 text-sm", status === t.k ? "bg-ink text-ink-foreground" : "text-muted-foreground hover:text-foreground")}>{t.l}</button>
          ))}
        </div>
      </PageHeader>
      <p className="-mt-4 mb-6 max-w-2xl text-sm text-muted-foreground">These are automated hypotheses, not conclusions. We can't see whether you actually use a tool — review each one and decide.</p>
      {error && <ErrorBox error={error} />}
      {isLoading ? <Loading /> : (
        <div className="grid gap-3">
          {data?.map((f) => (
            <Link key={f.id} to="/findings/$id" params={{ id: f.id }} className="grid gap-3 rounded-lg border bg-card p-5 transition hover:border-foreground/30 md:grid-cols-[1fr_auto]">
              <div>
                <div className="flex items-center gap-2 text-xs text-muted-foreground"><SeverityDot s={f.severity} />{findingTypeLabel[f.findingType]} · {f.subscriptionName} · {formatDate(f.createdAt)}</div>
                <div className="mt-1 font-display text-2xl">{f.title}</div>
                <p className="mt-1 text-sm text-muted-foreground">{f.explanation}</p>
              </div>
              <div className="flex items-center gap-4 md:flex-col md:items-end md:justify-between">
                <FindingStatusPill s={f.status} />
                <div className="tabular text-lg">{formatMoney(f.estimatedImpact)}</div>
                <Confidence v={f.confidence} />
              </div>
            </Link>
          ))}
          {data?.length === 0 && <div className="rounded-lg border border-dashed p-10 text-center text-sm text-muted-foreground">No findings here.</div>}
        </div>
      )}
    </AppShell>
  );
}
