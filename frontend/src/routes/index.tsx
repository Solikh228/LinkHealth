import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/app/AppShell";
import { OverviewPage } from "@/pages/OverviewPage";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Overview — SubTracker" },
      { name: "description", content: "Your recurring business spend, open findings, and upcoming renewals at a glance." },
      { property: "og:title", content: "Overview — SubTracker" },
      { property: "og:description", content: "Find hidden B2B subscriptions and auto-charges." },
    ],
  }),
  component: DashboardRoute,
});

function DashboardRoute() {
  return (
    <AppShell>
      <OverviewPage />
    </AppShell>
  );
}
