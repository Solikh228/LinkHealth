import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/app/AppShell";
import { WasteFinderPage } from "@/pages/WasteFinderPage";

export const Route = createFileRoute("/findings/")({
  head: () => ({
    meta: [
      { title: "Waste Finder — SubTracker" },
      { name: "description", content: "Evidence-backed potential waste: duplicates, price increases, forgotten tools." },
      { property: "og:title", content: "Waste Finder — SubTracker" },
      { property: "og:description", content: "Evidence-backed potential waste in your recurring spend." },
    ],
  }),
  component: WasteFinderRoute,
});

function WasteFinderRoute() {
  return (
    <AppShell>
      <WasteFinderPage />
    </AppShell>
  );
}
