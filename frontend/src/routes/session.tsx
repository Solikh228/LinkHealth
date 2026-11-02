import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/app/AppShell";
import { SessionPage } from "@/pages/SessionPage";

export const Route = createFileRoute("/session")({
  head: () => ({
    meta: [
      { title: "Collaborative Session — SubTracker" },
      { name: "description", content: "Real-time collaborative canvas session between interviewer and candidate." },
    ],
  }),
  component: SessionRoute,
});

function SessionRoute() {
  return (
    <AppShell>
      <SessionPage />
    </AppShell>
  );
}
