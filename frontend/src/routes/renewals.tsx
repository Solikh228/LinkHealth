import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/app/AppShell";
import { RenewalsPage } from "@/pages/RenewalsPage";

export const Route = createFileRoute("/renewals")({
  head: () => ({
    meta: [
      { title: "Renewals Timeline — SubTracker" },
      { name: "description", content: "Chronological schedule of upcoming subscription renewals and auto-charges." },
      { property: "og:title", content: "Renewals Timeline — SubTracker" },
      { property: "og:description", content: "Never get surprised by an auto-charge." },
    ],
  }),
  component: RenewalsRoute,
});

function RenewalsRoute() {
  return (
    <AppShell>
      <RenewalsPage />
    </AppShell>
  );
}
