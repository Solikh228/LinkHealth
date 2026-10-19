import { createFileRoute } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Landmark, Mail, RefreshCw } from "lucide-react";
import { AppShell, PageHeader } from "@/components/app/AppShell";
import { ErrorBox, Loading, Panel, SyncPill } from "@/components/app/bits";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api/client";
import { integrationsQuery } from "@/lib/api/queries";
import { formatDate } from "@/lib/money";

export const Route = createFileRoute("/integrations")({
  head: () => ({
    meta: [
      { title: "Connections — Ledgerline" },
      { name: "description", content: "Manage read-only bank and Gmail connections and their sync status." },
      { property: "og:title", content: "Connections — Ledgerline" },
      { property: "og:description", content: "Manage read-only bank and Gmail connections." },
    ],
  }),
  component: Integrations,
});

function Integrations() {
  const qc = useQueryClient();
  const { data, isLoading, error } = useQuery({ ...integrationsQuery(), refetchInterval: 3000 });
  const refresh = () => qc.invalidateQueries({ queryKey: ["api"] });
  const onErr = (e: Error) => toast.error(e.message);
  const bank = useMutation({ mutationFn: () => api.connectBank(), onSuccess: (r) => { if (r.redirectUrl) window.location.href = r.redirectUrl; else { refresh(); toast.success("Bank connected — initial sync started"); } }, onError: onErr });
  const gmail = useMutation({ mutationFn: () => api.connectGmail(), onSuccess: (r) => { if (r.redirectUrl) window.location.href = r.redirectUrl; else { refresh(); toast.success("Gmail connected"); } }, onError: onErr });
  const sync = useMutation({ mutationFn: (id: string) => api.syncIntegration(id), onSuccess: () => { refresh(); toast.success("Sync complete"); }, onError: onErr });
  const disconnect = useMutation({ mutationFn: ({ id, del }: { id: string; del: boolean }) => api.disconnectIntegration(id, del), onSuccess: () => { refresh(); toast.success("Disconnected"); }, onError: onErr });

  return (
    <AppShell>
      <PageHeader eyebrow="Read-only access" title="Connections">
        <Button variant="outline" onClick={() => gmail.mutate()} disabled={gmail.isPending}><Mail /> Connect Gmail</Button>
        <Button onClick={() => bank.mutate()} disabled={bank.isPending}><Landmark /> Connect bank</Button>
      </PageHeader>
      <p className="-mt-4 mb-6 max-w-2xl text-sm text-muted-foreground">You'll sign in with your bank or Google directly — we never see your bank password. We only read transactions and billing-related emails, and never move money.</p>
      {error && <ErrorBox error={error} />}
      {isLoading ? <Loading /> : (
        <div className="grid gap-4 md:grid-cols-2">
          {data?.map((c) => (
            <Panel key={c.id}>
              <div className="space-y-4 p-5">
                <div className="flex items-start gap-3">
                  <div className="rounded-md bg-muted p-2">{c.kind === "bank" ? <Landmark className="size-5" /> : <Mail className="size-5" />}</div>
                  <div className="flex-1">
                    <div className="font-medium">{c.displayName}</div>
                    <div className="text-xs capitalize text-muted-foreground">{c.provider} · {c.kind}</div>
                  </div>
                  <SyncPill s={c.syncState} />
                </div>
                <dl className="grid grid-cols-2 gap-2 text-xs">
                  <dt className="text-muted-foreground">Last sync</dt><dd>{c.lastSyncAt ? formatDate(c.lastSyncAt, { dateStyle: "medium", timeStyle: "short" }) : "—"}</dd>
                  <dt className="text-muted-foreground">Access granted</dt><dd className="font-mono">{c.scopesGranted.join(", ")}</dd>
                </dl>
                <div className="flex flex-wrap gap-2">
                  {c.status === "needs_reauth" ? (
                    <Button size="sm" onClick={() => (c.kind === "gmail" ? gmail.mutate() : bank.mutate())}>Reconnect</Button>
                  ) : (
                    <Button size="sm" variant="secondary" onClick={() => sync.mutate(c.id)} disabled={sync.isPending}><RefreshCw className={sync.isPending && sync.variables === c.id ? "animate-spin" : ""} /> Sync now</Button>
                  )}
                  <Button size="sm" variant="ghost" onClick={() => disconnect.mutate({ id: c.id, del: false })}>Disconnect</Button>
                  <Button size="sm" variant="ghost" className="text-destructive" onClick={() => confirm("Disconnect and delete all data imported from this connection?") && disconnect.mutate({ id: c.id, del: true })}>Disconnect & delete data</Button>
                </div>
              </div>
            </Panel>
          ))}
        </div>
      )}
    </AppShell>
  );
}
