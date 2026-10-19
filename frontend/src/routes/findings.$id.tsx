import { createFileRoute, Link } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { toast } from "sonner";
import { Mail, CreditCard } from "lucide-react";
import { AppShell, PageHeader } from "@/components/app/AppShell";
import { Confidence, ErrorBox, FindingStatusPill, Loading, Panel, Pill, SeverityDot, findingTypeLabel } from "@/components/app/bits";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { api } from "@/lib/api/client";
import { findingQuery } from "@/lib/api/queries";
import type { ReviewInput } from "@/lib/api/types";
import { formatDate, formatMoney, toMinor } from "@/lib/money";

export const Route = createFileRoute("/findings/$id")({
  head: () => ({
    meta: [
      { title: "Finding — Ledgerline" },
      { name: "description", content: "Review the evidence behind a potential-waste finding and record your decision." },
      { property: "og:title", content: "Finding — Ledgerline" },
      { property: "og:description", content: "Review the evidence behind a potential-waste finding." },
    ],
  }),
  component: FindingDetailPage,
});

const decisionLabel = { confirm: "Confirmed", dismiss: "Dismissed", mark_reviewing: "Marked for review", resolve: "Resolved" } as const;

function FindingDetailPage() {
  const { id } = Route.useParams();
  const qc = useQueryClient();
  const { data: f, isLoading, error } = useQuery(findingQuery(id));
  const [note, setNote] = useState("");
  const [savings, setSavings] = useState("");
  const review = useMutation({
    mutationFn: (decision: ReviewInput["decision"]) =>
      api.reviewFinding(id, {
        decision,
        note: note || undefined,
        estimatedSavings: savings && f?.estimatedImpact ? { amountMinor: toMinor(savings, f.estimatedImpact.currency), currency: f.estimatedImpact.currency } : undefined,
      }),
    onSuccess: (_, d) => { qc.invalidateQueries({ queryKey: ["api"] }); setNote(""); setSavings(""); toast.success(decisionLabel[d]); },
    onError: (e) => toast.error(e.message),
  });

  return (
    <AppShell>
      {error && <ErrorBox error={error} />}
      {isLoading || !f ? <Loading rows={6} /> : (
        <>
          <Link to="/findings" className="text-xs text-muted-foreground hover:text-foreground">← Findings</Link>
          <PageHeader eyebrow={findingTypeLabel[f.findingType]} title={f.title}><FindingStatusPill s={f.status} /></PageHeader>
          <div className="grid gap-6 lg:grid-cols-3">
            <div className="space-y-6 lg:col-span-2">
              <Panel title="Explanation">
                <div className="space-y-4 p-5">
                  <p className="leading-relaxed">{f.explanation}</p>
                  <div className="flex flex-wrap items-center gap-4 text-sm text-muted-foreground">
                    <span className="flex items-center gap-2"><SeverityDot s={f.severity} /> {f.severity} priority</span>
                    <Confidence v={f.confidence} />
                    <span>Estimated impact <span className="tabular text-foreground">{formatMoney(f.estimatedImpact)}</span></span>
                    <span className="font-mono text-xs">rule {f.ruleVersion}</span>
                  </div>
                  {f.subscriptionId && <Link to="/subscriptions/$id" params={{ id: f.subscriptionId }} className="inline-block text-sm text-primary hover:underline">Open {f.subscriptionName} →</Link>}
                </div>
              </Panel>
              <Panel title="Evidence">
                <ul className="divide-y">
                  {f.evidence.map((e, i) => (
                    <li key={i} className="flex gap-3 px-5 py-3 text-sm">
                      {e.email ? <Mail className="mt-0.5 size-4 text-muted-foreground" /> : <CreditCard className="mt-0.5 size-4 text-muted-foreground" />}
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2"><Pill t={e.role === "trigger" ? "ink" : "neutral"}>{e.role}</Pill><span className="truncate font-mono text-xs">{e.transaction?.descriptionRaw ?? e.email?.subjectMinimized}</span></div>
                        <div className="mt-1 text-xs text-muted-foreground">{e.explanation} · {formatDate(e.transaction?.postedAt ?? e.email?.receivedAt)}</div>
                      </div>
                      <div className="tabular">{formatMoney(e.transaction?.amount ?? e.email?.amount, { abs: true })}</div>
                    </li>
                  ))}
                  {f.evidence.length === 0 && <li className="px-5 py-6 text-sm text-muted-foreground">No evidence attached.</li>}
                </ul>
              </Panel>
            </div>
            <div className="space-y-6">
              <Panel title="Your decision">
                <div className="space-y-3 p-5">
                  <Textarea placeholder="Note (optional)" value={note} onChange={(e) => setNote(e.target.value)} />
                  <label className="block text-xs text-muted-foreground">Estimated savings per cycle ({f.estimatedImpact?.currency ?? "USD"})
                    <Input className="tabular mt-1" inputMode="decimal" placeholder="0.00" value={savings} onChange={(e) => setSavings(e.target.value)} />
                  </label>
                  <p className="text-xs text-muted-foreground">Savings you enter are tracked as your estimate — we never assume a subscription was cancelled.</p>
                  <div className="grid grid-cols-2 gap-2">
                    <Button onClick={() => review.mutate("confirm")} disabled={review.isPending}>Confirm</Button>
                    <Button variant="outline" onClick={() => review.mutate("dismiss")} disabled={review.isPending}>Dismiss</Button>
                    <Button variant="secondary" onClick={() => review.mutate("mark_reviewing")} disabled={review.isPending}>Review later</Button>
                    <Button variant="secondary" onClick={() => review.mutate("resolve")} disabled={review.isPending}>Resolved</Button>
                  </div>
                </div>
              </Panel>
              <Panel title="History">
                <ul className="divide-y text-sm">
                  {f.reviews.map((r) => (
                    <li key={r.id} className="px-5 py-3">
                      <div className="font-medium">{decisionLabel[r.decision]}</div>
                      <div className="text-xs text-muted-foreground">{formatDate(r.createdAt, { dateStyle: "medium", timeStyle: "short" })}{r.estimatedSavings && ` · est. savings ${formatMoney(r.estimatedSavings)}`}</div>
                      {r.note && <p className="mt-1 text-sm">{r.note}</p>}
                    </li>
                  ))}
                  <li className="px-5 py-3 text-xs text-muted-foreground">Detected automatically · {formatDate(f.createdAt)}</li>
                </ul>
              </Panel>
            </div>
          </div>
        </>
      )}
    </AppShell>
  );
}
