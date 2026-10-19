import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { AppShell, PageHeader } from "@/components/app/AppShell";
import { ErrorBox, Loading, Pill } from "@/components/app/bits";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { transactionsQuery } from "@/lib/api/queries";
import { formatDate, formatMoney } from "@/lib/money";

export const Route = createFileRoute("/transactions")({
  head: () => ({
    meta: [
      { title: "Transactions — Ledgerline" },
      { name: "description", content: "Imported bank transactions with recurring-charge flags." },
      { property: "og:title", content: "Transactions — Ledgerline" },
      { property: "og:description", content: "Imported bank transactions with recurring-charge flags." },
    ],
  }),
  component: Txs,
});

function Txs() {
  const [search, setSearch] = useState("");
  const [recurringOnly, setRecurringOnly] = useState(false);
  const { data, isLoading, error } = useQuery(transactionsQuery({ search, recurringOnly, limit: 100 }));
  return (
    <AppShell>
      <PageHeader eyebrow="Imported" title="Transactions">
        <Input placeholder="Search descriptor…" value={search} onChange={(e) => setSearch(e.target.value)} className="w-56 bg-card" />
        <label className="flex items-center gap-2 text-sm text-muted-foreground"><Switch checked={recurringOnly} onCheckedChange={setRecurringOnly} />Recurring only</label>
      </PageHeader>
      {error && <ErrorBox error={error} />}
      {isLoading ? <Loading /> : (
        <div className="overflow-x-auto rounded-lg border bg-card">
          <table className="w-full text-sm">
            <thead className="border-b text-left text-xs uppercase tracking-wider text-muted-foreground">
              <tr><th className="px-5 py-3 font-medium">Date</th><th className="px-3 font-medium">Statement descriptor</th><th className="px-3 font-medium">Matched to</th><th className="px-3 font-medium">Status</th><th className="px-5 text-right font-medium">Amount</th></tr>
            </thead>
            <tbody className="divide-y">
              {data?.items.map((t) => (
                <tr key={t.id} className="hover:bg-muted/40">
                  <td className="whitespace-nowrap px-5 py-2.5 text-muted-foreground">{formatDate(t.postedAt)}</td>
                  <td className="px-3 font-mono text-xs">{t.descriptionRaw}</td>
                  <td className="px-3">{t.subscriptionId ? <Link to="/subscriptions/$id" params={{ id: t.subscriptionId }} className="text-primary hover:underline">{t.merchantNormalized ?? "Unidentified"}</Link> : <span className="text-muted-foreground">—</span>}</td>
                  <td className="px-3">{t.status === "pending" ? <Pill t="warn">Pending</Pill> : <Pill>{t.status}</Pill>}</td>
                  <td className={`tabular px-5 text-right ${t.amount.amountMinor > 0 ? "text-success" : ""}`}>{formatMoney(t.amount)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="border-t px-5 py-3 text-xs text-muted-foreground">{data?.total} transactions</div>
        </div>
      )}
    </AppShell>
  );
}
