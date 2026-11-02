import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/app/AppShell";
import { SessionPage } from "@/pages/SessionPage";

export const Route = createFileRoute("/canvas")({
  head: () => ({
    meta: [
      { title: "Canvas — SubTracker" },
      { name: "description", content: "Real-time collaborative canvas session between interviewer and candidate." },
    ],
  }),
  component: CanvasRoute,
});

function CanvasRoute() {
  return (
    <AppShell>
      <SessionPage />
    </AppShell>
  );
}
