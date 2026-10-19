import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { ArrowRight } from "lucide-react";
import { AppShell, PageHeader } from "@/components/app/AppShell";
import { ErrorBox, Loading, Panel, Pill, SeverityDot, SyncPill, findingTypeLabel } from "@/components/app/bits";
import { dashboardQuery, findingsQuery } from "@/lib/api/queries";
import { formatDate, formatMoney, relativeDays } from "@/lib/money";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Overview — Ledgerline" },
      { name: "description", content: "Your recurring business spend, open findings, and upcoming renewals at a glance." },
      { property: "og:title", content: "Overview — Ledgerline" },
      { property: "og:description", content: "Find hidden B2B subscriptions and auto-charges." },
    ],
  }),
  component: Dashboard,
});

function Stat({ label, value, note }: { label: string; value: string; note?: string }) {
  return (
    <div className="px-5 py-5">
      <div className="text-xs uppercase tracking-[0.15em] text-muted-foreground">{label}</div>
      <div className="tabular mt-2 text-3xl font-medium">{value}</div>
      {note && <div className="mt-1 text-xs text-muted-foreground">{note}</div>}
    </div>
  );
}

function Dashboard() {
  const { data, isLoading, error } = useQuery(dashboardQuery());
  const { data: findings } = useQuery(findingsQuery({ status: "open" }));

  return (
    <AppShell>
      <PageHeader eyebrow="Overview" title={<>What's charging you, <em>and why.</em></>} />
      {error && <ErrorBox error={error} />}
      {isLoading || !data ? (
        <Loading rows={6} />
      ) : (
        <div className="space-y-6">
          <div className="grid grid-cols-2 divide-x divide-y rounded-lg border bg-card md:grid-cols-4 md:divide-y-0">
            <Stat label="Monthly recurring" value={formatMoney(data.monthlyRecurringSpend)} note="Estimate · annual plans ÷ 12" />
            <Stat label="Annualized" value={formatMoney(data.annualizedSpend)} note={`${data.subscriptionCount} subscriptions`} />
            <Stat label="Potential waste" value={formatMoney(data.potentialSavings)} note={`${data.openFindingsCount} open findings`} />
            <Stat label="Your estimated savings" value={formatMoney(data.userEstimatedSavings)} note="Entered by you, not verified" />
          </div>

          <div className="grid gap-6 lg:grid-cols-5">
            <Panel title="Needs your review" className="lg:col-span-3" action={<Link to="/findings" className="text-xs text-primary hover:underline">All findings</Link>}>
              <ul className="divide-y">
                {findings?.slice(0, 5).map((f) => (
                  <li key={f.id}>
                    <Link to="/findings/$id" params={{ id: f.id }} className="group flex items-start gap-3 px-5 py-4 hover:bg-muted/50">
                      <span className="pt-1.5"><SeverityDot s={f.severity} /></span>
                      <div className="min-w-0 flex-1">
                        <div className="text-xs text-muted-foreground">{findingTypeLabel[f.findingType]}</div>
                        <div className="font-medium">{f.title}</div>
                      </div>
                      <div className="tabular text-sm">{formatMoney(f.estimatedImpact)}</div>
                      <ArrowRight className="mt-1 size-4 text-muted-foreground opacity-0 transition group-hover:opacity-100" />
                    </Link>
                  </li>
                ))}
                {findings?.length === 0 && <li className="px-5 py-8 text-center text-sm text-muted-foreground">Nothing to review. Nice.</li>}
              </ul>
            </Panel>

            <Panel title="Upcoming charges" className="lg:col-span-2">
              <ul className="divide-y">
                {data.upcoming.map((u) => (
                  <li key={u.subscriptionId}>
                    <Link to="/subscriptions/$id" params={{ id: u.subscriptionId }} className="flex items-center justify-between px-5 py-3 hover:bg-muted/50">
                      <div>
                        <div className="text-sm font-medium">{u.name}</div>
                        <div className="text-xs text-muted-foreground">{formatDate(u.date)} · {relativeDays(u.date)}</div>
                      </div>
                      <div className="tabular text-sm">~{formatMoney(u.amount)}</div>
                    </Link>
                  </li>
                ))}
              </ul>
            </Panel>
          </div>

          <div className="grid gap-6 lg:grid-cols-3">
            <Panel title="Monthly spend by category">
              <ul className="space-y-3 p-5">
                {data.spendByCategory.map((c) => {
                  const pct = (c.monthly.amountMinor / Math.max(1, data.monthlyRecurringSpend.amountMinor)) * 100;
                  return (
                    <li key={c.category}>
                      <div className="flex justify-between text-sm"><span>{c.category}</span><span className="tabular">{formatMoney(c.monthly)}</span></div>
                      <div className="mt-1 h-1.5 rounded-full bg-muted"><div className="h-full rounded-full bg-primary" style={{ width: `${pct}%` }} /></div>
                    </li>
                  );
                })}
              </ul>
            </Panel>
            <Panel title="Recent changes">
              <ul className="divide-y">
                {data.recentChanges.map((c) => (
                  <li key={c.subscriptionId + c.kind} className="px-5 py-3">
                    <div className="flex items-center gap-2"><Pill t={c.kind === "new" ? "ink" : "warn"}>{c.kind === "new" ? "New" : "Price"}</Pill><span className="text-sm font-medium">{c.name}</span></div>
                    <div className="mt-1 text-xs text-muted-foreground">{c.detail} · {formatDate(c.date)}</div>
                  </li>
                ))}
              </ul>
            </Panel>
            <Panel title="Data connections" action={<Link to="/integrations" className="text-xs text-primary hover:underline">Manage</Link>}>
              <ul className="divide-y">
                {data.connections.map((c) => (
                  <li key={c.id} className="px-5 py-3">
                    <div className="text-sm font-medium">{c.displayName}</div>
                    <div className="mt-1 flex items-center gap-2"><SyncPill s={c.syncState} /><span className="text-xs text-muted-foreground">{c.lastSyncAt ? formatDate(c.lastSyncAt) : "Never"}</span></div>
                  </li>
                ))}
              </ul>
            </Panel>
          </div>
        </div>
      )}
    </AppShell>
  );
}
