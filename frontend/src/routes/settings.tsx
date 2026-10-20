import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useMutation, useQuery } from "@tanstack/react-query";
import { AppShell, PageHeader } from "@/components/app/AppShell";
import { Panel } from "@/components/app/bits";
import { Button } from "@/components/ui/button";
import { API_MODE, api, tokenStore } from "@/lib/api/client";
import { meQuery } from "@/lib/api/queries";

export const Route = createFileRoute("/settings")({
  head: () => ({
    meta: [
      { title: "Settings — Ledgerline" },
      { name: "description", content: "Account, workspace, and data-deletion settings." },
      { property: "og:title", content: "Settings — Ledgerline" },
      { property: "og:description", content: "Account, workspace, and data-deletion settings." },
    ],
  }),
  component: Settings,
});

function Settings() {
  const nav = useNavigate();
  const { data: me } = useQuery(meQuery());
  const { data: ws } = useQuery({ queryKey: ["api", "workspace"], queryFn: () => api.getWorkspace() });
  const del = useMutation({ mutationFn: () => api.deleteAccount(), onSuccess: () => { tokenStore.clear(); nav({ to: "/login" }); } });
  return (
    <AppShell>
      <PageHeader eyebrow="Account" title="Settings" />
      <div className="grid max-w-2xl gap-6">
        <Panel title="Profile">
          <dl className="grid grid-cols-[140px_1fr] gap-3 p-5 text-sm">
            <dt className="text-muted-foreground">Email</dt><dd>{me?.email}</dd>
            <dt className="text-muted-foreground">Workspace</dt><dd>{ws?.name}</dd>
            <dt className="text-muted-foreground">Base currency</dt><dd>{ws?.baseCurrency}</dd>
            <dt className="text-muted-foreground">Backend</dt><dd className="font-mono">{API_MODE === "mock" ? "mock (in-browser)" : (import.meta.env["VITE_API_BASE_URL"] ?? "http://localhost:8091")}</dd>
          </dl>
          <div className="border-t p-5"><Button variant="outline" onClick={() => { tokenStore.clear(); nav({ to: "/login" }); }}>Sign out</Button></div>
        </Panel>
        <Panel title="Danger zone">
          <div className="space-y-3 p-5">
            <p className="text-sm text-muted-foreground">Deletes your account, disconnects all integrations, and removes imported transactions and email evidence.</p>
            <Button variant="destructive" disabled={del.isPending} onClick={() => confirm("Permanently delete your account and all data?") && del.mutate()}>Delete account</Button>
          </div>
        </Panel>
      </div>
    </AppShell>
  );
}
