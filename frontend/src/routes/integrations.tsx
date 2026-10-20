import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/app/AppShell";
import { ConnectionsPage } from "@/pages/ConnectionsPage";

export const Route = createFileRoute("/integrations")({
  head: () => ({
    meta: [
      { title: "Connections — SubTracker" },
      { name: "description", content: "Manage read-only bank and Gmail connections and data privacy controls." },
      { property: "og:title", content: "Connections — SubTracker" },
      { property: "og:description", content: "Manage read-only bank and Gmail connections." },
    ],
  }),
  component: ConnectionsRoute,
});

function ConnectionsRoute() {
  return (
    <AppShell>
      <ConnectionsPage />
    </AppShell>
  );
}
