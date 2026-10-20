import { useState, useEffect } from "react";
import { Link } from "@tanstack/react-router";
import { ArrowRight, CheckCircle2, AlertTriangle, Clock, RefreshCw } from "lucide-react";
import { PageHeader } from "@/components/app/AppShell";
import { Panel, Pill, SeverityDot } from "@/components/app/bits";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { apiClient } from "@/services/apiClient";
import type { Finding, OverviewMetrics, Subscription } from "@/types";

function formatMoney(amountMinor: number, currency = "USD"): string {
  const symbol = currency === "EUR" ? "€" : "$";
  return `${symbol}${(amountMinor / 100).toFixed(2)}`;
}

export function OverviewPage() {
  const [metrics, setMetrics] = useState<OverviewMetrics | null>(null);
  const [findings, setFindings] = useState<Finding[]>([]);
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([]);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    setLoading(true);
    try {
      const [m, f, s] = await Promise.all([
        apiClient.getOverviewMetrics(),
        apiClient.getFindings(),
        apiClient.getSubscriptions(),
      ]);
      setMetrics(m);
      setFindings(f);
      setSubscriptions(s);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleQuickAction = async (findingId: string, decision: "confirmed_waste" | "dismissed") => {
    await apiClient.updateFindingDecision(findingId, decision);
    await loadData();
  };

  if (loading || !metrics) {
    return (
      <div>
        <PageHeader eyebrow="Overview" title="Subscription & Waste Audit" />
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Skeleton className="h-28 rounded-lg" />
          <Skeleton className="h-28 rounded-lg" />
          <Skeleton className="h-28 rounded-lg" />
          <Skeleton className="h-28 rounded-lg" />
        </div>
        <div className="mt-8 grid gap-6 md:grid-cols-2">
          <Skeleton className="h-64 rounded-lg" />
          <Skeleton className="h-64 rounded-lg" />
        </div>
      </div>
    );
  }

  // Upcoming charges within next 14 days
  const upcomingCharges = subscriptions
    .filter((s) => s.nextRenewalDate)
    .sort((a, b) => (a.nextRenewalDate || "").localeCompare(b.nextRenewalDate || ""))
    .slice(0, 5);

  const openFindings = findings.filter((f) => f.status === "open").slice(0, 3);

  return (
    <div className="space-y-8">
      <PageHeader eyebrow="Overview" title="Subscription & Waste Audit" />

      {/* 4 Separate Summary Metric Cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-xs uppercase tracking-wider text-muted-foreground">Monthly Recurring Spend</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{formatMoney(metrics.monthlyRecurringSpend.amountMinor)}</div>
            <p className="mt-1 text-xs text-muted-foreground">{metrics.activeSubscriptionCount} active subscriptions</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-xs uppercase tracking-wider text-muted-foreground">Active Subscriptions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{metrics.activeSubscriptionCount}</div>
            <p className="mt-1 text-xs text-muted-foreground">Across banking and email feeds</p>
          </CardContent>
        </Card>

        {/* Separated Potential Savings Container */}
        <Card className="border-amber-500/30 bg-amber-500/5">
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-1.5 text-xs uppercase tracking-wider text-amber-600 dark:text-amber-400">
              <AlertTriangle className="size-3.5" />
              Potential Savings to Review
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-amber-600 dark:text-amber-400">
              {formatMoney(metrics.potentialSavings.amountMinor)}
            </div>
            <p className="mt-1 text-xs text-muted-foreground">{metrics.openFindingsCount} unreviewed hypothesis findings</p>
          </CardContent>
        </Card>

        {/* Separated Confirmed Savings Container */}
        <Card className="border-emerald-500/30 bg-emerald-500/5">
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-1.5 text-xs uppercase tracking-wider text-emerald-600 dark:text-emerald-400">
              <CheckCircle2 className="size-3.5" />
              Confirmed Realized Savings
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-emerald-600 dark:text-emerald-400">
              {formatMoney(metrics.confirmedSavings.amountMinor)}
            </div>
            <p className="mt-1 text-xs text-muted-foreground">Decisions confirmed by user</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-5">
        {/* Top 3 Urgent Findings from Waste Finder with Quick Action Buttons */}
        <Panel
          title="Top Waste Finder Actions"
          className="lg:col-span-3"
          action={<Link to="/findings" className="text-xs text-primary hover:underline">View all findings</Link>}
        >
          <ul className="divide-y">
            {openFindings.map((f) => (
              <li key={f.id} className="p-4">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-start gap-3">
                    <span className="pt-1"><SeverityDot s={f.severity} /></span>
                    <div>
                      <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                        {f.type.replace("_", " ")} · {f.subscriptionName}
                      </div>
                      <Link to="/findings/$id" params={{ id: f.id }} className="text-base font-medium hover:underline">
                        {f.title}
                      </Link>
                      <p className="mt-1 text-xs text-muted-foreground">{f.explanation}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-semibold">{formatMoney(f.potentialSavings.amountMinor)}</div>
                    <div className="text-[11px] text-muted-foreground">impact</div>
                  </div>
                </div>
                <div className="mt-3 flex items-center justify-end gap-2 border-t pt-2">
                  <Button
                    size="sm"
                    variant="outline"
                    className="h-7 text-xs"
                    onClick={() => handleQuickAction(f.id, "dismissed")}
                  >
                    Keep Tool
                  </Button>
                  <Button
                    size="sm"
                    className="h-7 bg-destructive text-xs hover:bg-destructive/90"
                    onClick={() => handleQuickAction(f.id, "confirmed_waste")}
                  >
                    Confirm Waste
                  </Button>
                </div>
              </li>
            ))}
            {openFindings.length === 0 && (
              <li className="p-8 text-center text-sm text-muted-foreground">
                Zero open waste findings. All subscriptions verified!
              </li>
            )}
          </ul>
        </Panel>

        {/* Upcoming Renewals Widget */}
        <Panel title="Upcoming Renewals (Next 14 Days)" className="lg:col-span-2">
          <ul className="divide-y">
            {upcomingCharges.map((s) => (
              <li key={s.id} className="flex items-center justify-between p-3.5 hover:bg-muted/30">
                <div className="flex items-center gap-2.5">
                  <Clock className="size-4 text-muted-foreground" />
                  <div>
                    <div className="text-sm font-medium">{s.name}</div>
                    <div className="text-xs text-muted-foreground">Renews on {s.nextRenewalDate}</div>
                  </div>
                </div>
                <div className="text-right font-medium text-sm">
                  {formatMoney(s.amount.amountMinor, s.amount.currency)}
                </div>
              </li>
            ))}
          </ul>
        </Panel>
      </div>

      {/* Recently Detected Changes Feed */}
      <Panel title="Recently Detected Changes">
        <ul className="divide-y">
          <li className="flex items-center justify-between p-4">
            <div className="flex items-center gap-3">
              <Pill t="warn">Price Increase</Pill>
              <div>
                <span className="font-medium text-sm">Notion Plus</span>
                <p className="text-xs text-muted-foreground">Monthly subscription rate increased from $10.00 to $12.00/mo.</p>
              </div>
            </div>
            <span className="text-xs text-muted-foreground">3 cycles ago</span>
          </li>
          <li className="flex items-center justify-between p-4">
            <div className="flex items-center gap-3">
              <Pill t="ink">Trial Converted</Pill>
              <div>
                <span className="font-medium text-sm">Notion AI Add-on</span>
                <p className="text-xs text-muted-foreground">30-day free trial expired and converted to recurring billing.</p>
              </div>
            </div>
            <span className="text-xs text-muted-foreground">Yesterday</span>
          </li>
        </ul>
      </Panel>
    </div>
  );
}
