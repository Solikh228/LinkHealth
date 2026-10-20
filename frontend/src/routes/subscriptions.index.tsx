import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/app/AppShell";
import { SubscriptionsPage } from "@/pages/SubscriptionsPage";

export const Route = createFileRoute("/subscriptions/")({
  head: () => ({
    meta: [
      { title: "Subscriptions — SubTracker" },
      { name: "description", content: "Every recurring charge detected across your bank and email." },
      { property: "og:title", content: "Subscriptions — SubTracker" },
      { property: "og:description", content: "Every recurring charge detected across your bank and email." },
    ],
  }),
  component: SubscriptionsRoute,
});

function SubscriptionsRoute() {
  return (
    <AppShell>
      <SubscriptionsPage />
    </AppShell>
  );
}
