import { cn } from "@/lib/utils";
import type { FindingStatus, FindingType, Severity, SubscriptionStatus, SyncState } from "@/lib/api/types";
import { Skeleton } from "@/components/ui/skeleton";

const tone = {
  neutral: "bg-muted text-muted-foreground",
  good: "bg-success/15 text-success",
  warn: "bg-warning/25 text-warning-foreground",
  bad: "bg-destructive/12 text-destructive",
  ink: "bg-ink text-ink-foreground",
} as const;

export function Pill({ t = "neutral", children, className }: { t?: keyof typeof tone; children: React.ReactNode; className?: string }) {
  return <span className={cn("inline-flex items-center gap-1 rounded-sm px-2 py-0.5 text-xs font-medium", tone[t], className)}>{children}</span>;
}

export function SubStatus({ s }: { s: SubscriptionStatus }) {
  const m = { candidate: ["warn", "Needs review"], confirmed: ["good", "Confirmed"], dismissed: ["neutral", "Dismissed"], inactive: ["neutral", "Inactive"] } as const;
  return <Pill t={m[s][0]}>{m[s][1]}</Pill>;
}

export function FindingStatusPill({ s }: { s: FindingStatus }) {
  const m = { new: ["ink", "New"], reviewing: ["warn", "Reviewing"], confirmed: ["good", "Confirmed"], dismissed: ["neutral", "Dismissed"], resolved: ["good", "Resolved"] } as const;
  return <Pill t={m[s][0]}>{m[s][1]}</Pill>;
}

export function SeverityDot({ s }: { s: Severity }) {
  return <span className={cn("inline-block size-2 rounded-full", s === "high" ? "bg-destructive" : s === "medium" ? "bg-warning" : "bg-muted-foreground/50")} aria-label={`${s} severity`} />;
}

export const findingTypeLabel: Record<FindingType, string> = {
  possible_duplicate: "Possible duplicate",
  price_increase: "Price increase",
  unexpected_charge: "Unexpected charge",
  low_evidence: "Possibly forgotten",
  renewal_approaching: "Renewal approaching",
  unclear_vendor: "Unclear vendor",
};

export const syncLabel: Record<SyncState, [keyof typeof tone, string]> = {
  not_connected: ["neutral", "Not connected"],
  connecting: ["warn", "Connecting"],
  initial_sync: ["warn", "Initial sync in progress"],
  up_to_date: ["good", "Up to date"],
  delayed: ["warn", "Sync delayed"],
  needs_reauth: ["bad", "Needs reauthorization"],
  error: ["bad", "Error — action needed"],
  disconnected: ["neutral", "Disconnected"],
};

export function SyncPill({ s }: { s: SyncState }) {
  return <Pill t={syncLabel[s][0]}>{syncLabel[s][1]}</Pill>;
}

export function Confidence({ v }: { v: number }) {
  const pct = Math.round(v * 100);
  return (
    <span className="inline-flex items-center gap-2" title={`${pct}% detection confidence`}>
      <span className="h-1.5 w-12 overflow-hidden rounded-full bg-muted">
        <span className={cn("block h-full", v >= 0.85 ? "bg-primary" : v >= 0.65 ? "bg-warning" : "bg-destructive")} style={{ width: `${pct}%` }} />
      </span>
      <span className="tabular text-xs text-muted-foreground">{pct}%</span>
    </span>
  );
}

export function Loading({ rows = 4 }: { rows?: number }) {
  return (
    <div className="space-y-3">
      {Array.from({ length: rows }).map((_, i) => (
        <Skeleton key={i} className="h-14 w-full bg-muted" />
      ))}
    </div>
  );
}

export function ErrorBox({ error }: { error: unknown }) {
  return <div className="rounded-md border border-destructive/40 bg-destructive/5 p-4 text-sm text-destructive">{error instanceof Error ? error.message : "Something went wrong"}</div>;
}

export function Panel({ title, children, action, className }: { title?: string; children: React.ReactNode; action?: React.ReactNode; className?: string }) {
  return (
    <section className={cn("rounded-lg border bg-card", className)}>
      {title && (
        <div className="flex items-center justify-between border-b px-5 py-3">
          <h2 className="text-xs font-semibold uppercase tracking-[0.15em] text-muted-foreground">{title}</h2>
          {action}
        </div>
      )}
      <div>{children}</div>
    </section>
  );
}

export const intervalLabel = { weekly: "Weekly", monthly: "Monthly", quarterly: "Quarterly", annual: "Annual", irregular: "Irregular", unknown: "Unknown" } as const;
