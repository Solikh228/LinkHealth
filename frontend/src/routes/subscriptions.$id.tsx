import { createFileRoute, Link } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Check, X } from "lucide-react";
import { AppShell, PageHeader } from "@/components/app/AppShell";
import { Confidence, ErrorBox, FindingStatusPill, Loading, Panel, Pill, SubStatus, intervalLabel, findingTypeLabel } from "@/components/app/bits";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { api } from "@/lib/api/client";
import { subscriptionQuery } from "@/lib/api/queries";
import type { BillingInterval } from "@/lib/api/types";
import { formatDate, formatMoney, toMinor } from "@/lib/money";

export const Route = createFileRoute("/subscriptions/$id")({
  head: () => ({
    meta: [
      { title: "Subscription detail — Ledgerline" },
      { name: "description", content: "Charge history, matched invoices, and detection rationale for a subscription." },
      { property: "og:title", content: "Subscription detail — Ledgerline" },
      { property: "og:description", content: "Charge history, matched invoices, and detection rationale." },
    ],
  }),
  component: SubDetail,
});

function SubDetail() {
  const { id } = Route.useParams();
  const qc = useQueryClient();
  const { data: s, isLoading, error } = useQuery(subscriptionQuery(id));
  const [form, setForm] = useState({ displayName: "", interval: "monthly" as BillingInterval, amount: "", note: "" });
  useEffect(() => {
    if (s) setForm({ displayName: s.displayName, interval: s.billingInterval, amount: s.expectedAmount ? String(s.expectedAmount.amountMinor / 100) : "", note: s.note ?? "" });
  }, [s]);
  const done = (msg: string) => { qc.invalidateQueries({ queryKey: ["api"] }); toast.success(msg); };
  const confirm = useMutation({ mutationFn: () => api.confirmSubscription(id), onSuccess: () => done("Marked as confirmed subscription") });
  const dismiss = useMutation({ mutationFn: () => api.dismissSubscription(id), onSuccess: () => done("Dismissed — not a subscription") });
  const save = useMutation({
    mutationFn: () => api.updateSubscription(id, {
      displayName: form.displayName,
      billingInterval: form.interval,
      note: form.note,
      ...(form.amount && s?.expectedAmount ? { expectedAmount: { amountMinor: toMinor(form.amount, s.expectedAmount.currency), currency: s.expectedAmount.currency } } : {}),
    }),
    onSuccess: () => done("Corrections saved"),
  });

  return (
    <AppShell>
      {error && <ErrorBox error={error} />}
      {isLoading || !s ? <Loading rows={6} /> : (
        <>
          <Link to="/subscriptions" className="text-xs text-muted-foreground hover:text-foreground">← Subscriptions</Link>
          <PageHeader eyebrow={`${s.category ?? "Uncategorized"}${s.vendorDomain ? " · " + s.vendorDomain : ""}`} title={s.displayName}>
            <Button variant="outline" onClick={() => dismiss.mutate()} disabled={dismiss.isPending || s.status === "dismissed"}><X /> Not a subscription</Button>
            <Button onClick={() => confirm.mutate()} disabled={confirm.isPending || s.status === "confirmed"}><Check /> Confirm</Button>
          </PageHeader>

          <div className="mb-6 grid grid-cols-2 divide-x rounded-lg border bg-card md:grid-cols-4">
            {[
              ["Expected amount", <span className="tabular">{formatMoney(s.expectedAmount)}</span>, "Estimate"],
              ["Interval", intervalLabel[s.billingInterval], `≈ ${formatMoney(s.monthlyEquivalent)} / mo`],
              ["Next charge", formatDate(s.estimatedNextChargeAt), "Estimated"],
              ["Status", <SubStatus s={s.status} />, <Confidence v={s.detectionConfidence} />],
            ].map(([l, v, n], i) => (
              <div key={i} className="px-5 py-4">
                <div className="text-xs uppercase tracking-[0.15em] text-muted-foreground">{l}</div>
                <div className="mt-2 text-xl">{v}</div>
                <div className="mt-1 text-xs text-muted-foreground">{n}</div>
              </div>
            ))}
          </div>

          <div className="grid gap-6 lg:grid-cols-3">
            <div className="space-y-6 lg:col-span-2">
              <Panel title="Why we think this is recurring">
                <p className="p-5 text-sm leading-relaxed">{s.detectionExplanation}</p>
              </Panel>
              <Panel title={`Charge history (${s.transactions.length})`}>
                <ul className="divide-y">
                  {s.transactions.map((t) => (
                    <li key={t.id} className="flex items-center justify-between px-5 py-3 text-sm">
                      <div><div className="font-mono text-xs">{t.descriptionRaw}</div><div className="text-xs text-muted-foreground">{formatDate(t.postedAt)} · {t.accountName}</div></div>
                      <div className="tabular">{formatMoney(t.amount, { abs: true })}</div>
                    </li>
                  ))}
                </ul>
              </Panel>
              <Panel title={`Email evidence (${s.evidence.length})`}>
                {s.evidence.length === 0 ? <p className="p-5 text-sm text-muted-foreground">No matching invoices or receipts found in Gmail.</p> : (
                  <ul className="divide-y">
                    {s.evidence.map((e) => (
                      <li key={e.id} className="flex items-center justify-between gap-3 px-5 py-3 text-sm">
                        <div className="min-w-0">
                          <div className="truncate">{e.subjectMinimized}</div>
                          <div className="text-xs text-muted-foreground">{e.senderDomain} · {formatDate(e.receivedAt)} · {e.matchReason}</div>
                        </div>
                        <div className="flex shrink-0 items-center gap-3">
                          <Pill t={e.matchStatus === "confirmed" ? "good" : "warn"}>{e.matchStatus}</Pill>
                          <span className="tabular">{formatMoney(e.amount)}</span>
                        </div>
                      </li>
                    ))}
                  </ul>
                )}
              </Panel>
            </div>
            <div className="space-y-6">
              <Panel title="Correct details">
                <form className="space-y-3 p-5" onSubmit={(e) => { e.preventDefault(); save.mutate(); }}>
                  <label className="block text-xs text-muted-foreground">Name<Input className="mt-1" value={form.displayName} onChange={(e) => setForm({ ...form, displayName: e.target.value })} /></label>
                  <label className="block text-xs text-muted-foreground">Interval
                    <select className="mt-1 h-9 w-full rounded-md border bg-card px-2 text-sm text-foreground" value={form.interval} onChange={(e) => setForm({ ...form, interval: e.target.value as BillingInterval })}>
                      {Object.entries(intervalLabel).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                    </select>
                  </label>
                  <label className="block text-xs text-muted-foreground">Amount ({s.expectedAmount?.currency})<Input className="tabular mt-1" inputMode="decimal" value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} /></label>
                  <label className="block text-xs text-muted-foreground">Note<Textarea className="mt-1" value={form.note} onChange={(e) => setForm({ ...form, note: e.target.value })} /></label>
                  <Button type="submit" variant="secondary" className="w-full" disabled={save.isPending}>Save corrections</Button>
                </form>
              </Panel>
              {s.findings.length > 0 && (
                <Panel title="Related findings">
                  <ul className="divide-y">
                    {s.findings.map((f) => (
                      <li key={f.id}><Link to="/findings/$id" params={{ id: f.id }} className="block px-5 py-3 hover:bg-muted/50">
                        <div className="flex items-center justify-between"><span className="text-xs text-muted-foreground">{findingTypeLabel[f.findingType]}</span><FindingStatusPill s={f.status} /></div>
                        <div className="mt-1 text-sm font-medium">{f.title}</div>
                      </Link></li>
                    ))}
                  </ul>
                </Panel>
              )}
            </div>
          </div>
        </>
      )}
    </AppShell>
  );
}
