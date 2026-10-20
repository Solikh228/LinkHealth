import { useState, useEffect, useMemo } from "react";
import { Search, SlidersHorizontal, Check, AlertCircle, RefreshCw } from "lucide-react";
import { PageHeader } from "@/components/app/AppShell";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { apiClient } from "@/services/apiClient";
import { SubscriptionDetailDrawer } from "@/components/subscriptions/SubscriptionDetailDrawer";
import type { Subscription } from "@/types";

export function SubscriptionsPage() {
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [cadenceFilter, setCadenceFilter] = useState("all");
  const [selectedSub, setSelectedSub] = useState<Subscription | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);

  const fetchSubs = async () => {
    setLoading(true);
    try {
      const data = await apiClient.getSubscriptions();
      setSubscriptions(data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSubs();
  }, []);

  const filteredSubs = useMemo(() => {
    return subscriptions.filter((s) => {
      const matchesSearch = s.name.toLowerCase().includes(search.toLowerCase()) ||
        (s.vendorDomain && s.vendorDomain.toLowerCase().includes(search.toLowerCase()));

      let matchesStatus = true;
      if (statusFilter === "needs_review") matchesStatus = s.status === "candidate";
      else if (statusFilter === "useful") matchesStatus = s.status === "active";
      else if (statusFilter === "potential_waste") matchesStatus = s.status === "confirmed";
      else if (statusFilter === "cancelled") matchesStatus = s.status === "cancelled";

      const matchesCadence = cadenceFilter === "all" || s.billingInterval === cadenceFilter;

      return matchesSearch && matchesStatus && matchesCadence;
    });
  }, [subscriptions, search, statusFilter, cadenceFilter]);

  const handleRowClick = (sub: Subscription) => {
    setSelectedSub(sub);
    setDrawerOpen(true);
  };

  const handleSaveSub = (updated: Subscription) => {
    setSubscriptions((prev) => prev.map((s) => (s.id === updated.id ? updated : s)));
    setSelectedSub(updated);
  };

  const renderStatusBadge = (status: Subscription["status"]) => {
    switch (status) {
      case "candidate":
        return <Badge variant="outline" className="border-amber-500/50 bg-amber-500/10 text-amber-600 dark:text-amber-400">Needs Review</Badge>;
      case "active":
        return <Badge variant="outline" className="border-emerald-500/50 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">Useful</Badge>;
      case "confirmed":
        return <Badge variant="outline" className="border-destructive/50 bg-destructive/10 text-destructive">Potential Waste</Badge>;
      case "cancelled":
        return <Badge variant="outline" className="border-muted text-muted-foreground">Cancelled</Badge>;
      default:
        return <Badge variant="outline">Active</Badge>;
    }
  };

  const renderEvidenceBadge = (sub: Subscription) => {
    if (sub.vendorDomain && sub.id !== "sub_unknown") {
      return <Badge variant="secondary" className="text-[11px]">Both (Bank + Email)</Badge>;
    }
    return <Badge variant="outline" className="text-[11px]">Bank Only</Badge>;
  };

  return (
    <div className="space-y-6">
      <PageHeader eyebrow="Detected" title="Subscriptions" />

      {/* Search and Filters */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search vendor name or domain..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>

        <div className="flex items-center gap-2">
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="w-[150px]">
              <SelectValue placeholder="All Statuses" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Statuses</SelectItem>
              <SelectItem value="needs_review">Needs Review</SelectItem>
              <SelectItem value="useful">Useful</SelectItem>
              <SelectItem value="potential_waste">Potential Waste</SelectItem>
              <SelectItem value="cancelled">Cancelled</SelectItem>
            </SelectContent>
          </Select>

          <Select value={cadenceFilter} onValueChange={setCadenceFilter}>
            <SelectTrigger className="w-[140px]">
              <SelectValue placeholder="All Cadences" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Cadences</SelectItem>
              <SelectItem value="monthly">Monthly</SelectItem>
              <SelectItem value="annual">Annual</SelectItem>
              <SelectItem value="quarterly">Quarterly</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Subscriptions Table */}
      {loading ? (
        <div className="space-y-2">
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-14 w-full" />
          <Skeleton className="h-14 w-full" />
          <Skeleton className="h-14 w-full" />
        </div>
      ) : (
        <div className="overflow-x-auto rounded-lg border bg-card">
          <table className="w-full text-sm">
            <thead className="border-b bg-muted/30 text-left text-xs uppercase tracking-wider text-muted-foreground">
              <tr>
                <th className="px-5 py-3 font-medium">Vendor</th>
                <th className="px-3 py-3 font-medium text-right">Amount</th>
                <th className="px-3 py-3 font-medium">Cadence</th>
                <th className="px-3 py-3 font-medium">Last Charge</th>
                <th className="px-3 py-3 font-medium">Next Charge</th>
                <th className="px-3 py-3 font-medium">Evidence Source</th>
                <th className="px-3 py-3 font-medium">Confidence</th>
                <th className="px-5 py-3 font-medium">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {filteredSubs.map((sub) => (
                <tr
                  key={sub.id}
                  onClick={() => handleRowClick(sub)}
                  className="cursor-pointer transition hover:bg-muted/40"
                >
                  <td className="px-5 py-3">
                    <div className="font-medium text-foreground">{sub.name}</div>
                    {sub.vendorDomain && (
                      <div className="text-xs text-muted-foreground">{sub.vendorDomain}</div>
                    )}
                  </td>
                  <td className="px-3 py-3 text-right font-medium">
                    ${(sub.amount.amountMinor / 100).toFixed(2)}
                    {sub.billingInterval === "annual" && (
                      <div className="text-[11px] text-muted-foreground">
                        ~${(sub.monthlyEquivalent.amountMinor / 100).toFixed(2)}/mo
                      </div>
                    )}
                  </td>
                  <td className="px-3 py-3 capitalize">{sub.billingInterval}</td>
                  <td className="px-3 py-3 text-muted-foreground">{sub.lastChargeDate}</td>
                  <td className="px-3 py-3 font-medium text-foreground">{sub.nextRenewalDate ?? "—"}</td>
                  <td className="px-3 py-3">{renderEvidenceBadge(sub)}</td>
                  <td className="px-3 py-3">
                    <span className="font-mono text-xs font-medium">
                      {Math.round(sub.confidence * 100)}%
                    </span>
                  </td>
                  <td className="px-5 py-3">{renderStatusBadge(sub.status)}</td>
                </tr>
              ))}
              {filteredSubs.length === 0 && (
                <tr>
                  <td colSpan={8} className="p-8 text-center text-sm text-muted-foreground">
                    No subscriptions match your filter criteria.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Detail Slide-over Drawer */}
      <SubscriptionDetailDrawer
        subscription={selectedSub}
        open={drawerOpen}
        onOpenChange={setDrawerOpen}
        onSave={handleSaveSub}
      />
    </div>
  );
}
