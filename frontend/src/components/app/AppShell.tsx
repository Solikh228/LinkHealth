import { Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { LayoutDashboard, Repeat, AlertTriangle, ReceiptText, Plug, Settings, Clock } from "lucide-react";
import type { ReactNode } from "react";
import { API_MODE } from "@/lib/api/client";
import { findingsQuery, meQuery } from "@/lib/api/queries";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";

const nav = [
  { to: "/", label: "Overview", icon: LayoutDashboard },
  { to: "/subscriptions", label: "Subscriptions", icon: Repeat },
  { to: "/findings", label: "Waste Finder", icon: AlertTriangle },
  { to: "/renewals", label: "Renewals", icon: Clock },
  { to: "/transactions", label: "Transactions", icon: ReceiptText },
  { to: "/integrations", label: "Connections", icon: Plug },
  { to: "/settings", label: "Settings", icon: Settings },
] as const;

export function AppShell({ children }: { children: ReactNode }) {
  const { data: open } = useQuery(findingsQuery({ status: "open" }));
  const { data: me } = useQuery(meQuery());
  const initials = (me?.email ?? "Alex")[0].toUpperCase();

  return (
    <div className="flex min-h-screen">
      <aside className="sticky top-0 hidden h-screen w-60 shrink-0 flex-col bg-sidebar text-sidebar-foreground md:flex">
        <div className="px-6 pb-8 pt-7">
          <div className="font-display text-3xl leading-none text-sidebar-accent-foreground">SubTracker</div>
          <div className="mt-1 text-xs uppercase tracking-[0.2em] text-sidebar-foreground/60">Subscription & Waste Audit</div>
        </div>
        <nav className="flex flex-1 flex-col gap-0.5 px-3">
          {nav.map(({ to, label, icon: Icon }) => (
            <Link
              key={to}
              to={to}
              activeOptions={{ exact: to === "/" }}
              className="flex items-center gap-3 rounded-md px-3 py-2 text-sm text-sidebar-foreground/80 transition-colors hover:bg-sidebar-accent hover:text-sidebar-accent-foreground data-[status=active]:bg-sidebar-accent data-[status=active]:text-sidebar-accent-foreground"
            >
              <Icon className="size-4" />
              <span className="flex-1">{label}</span>
              {to === "/findings" && open && open.length > 0 && (
                <span className="tabular rounded-sm bg-sidebar-primary px-1.5 text-xs text-sidebar-primary-foreground">{open.length}</span>
              )}
            </Link>
          ))}
        </nav>
        <div className="border-t border-sidebar-border px-6 py-4">
          <div className="flex items-center gap-3">
            <Avatar className="size-8">
              <AvatarFallback className="bg-sidebar-accent text-sidebar-accent-foreground text-xs font-medium">
                {initials}
              </AvatarFallback>
            </Avatar>
            <div className="min-w-0 flex-1">
              <div className="truncate text-xs font-medium text-sidebar-foreground">{me?.email ?? "alex@studio.dev"}</div>
              {API_MODE === "mock" ? (
                <div className="text-[11px] text-sidebar-primary">Mock backend</div>
              ) : (
                <div className="font-mono text-[11px] text-sidebar-foreground/50">Backend: SQLite (:8091)</div>
              )}
            </div>
          </div>
        </div>
      </aside>
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center justify-between border-b bg-card px-4 py-3 md:hidden">
          <div className="font-display text-2xl font-bold">SubTracker</div>
          <Avatar className="size-8">
            <AvatarFallback className="bg-muted text-xs font-medium">{initials}</AvatarFallback>
          </Avatar>
        </header>
        <nav className="flex gap-1 overflow-x-auto border-b bg-card px-3 py-2 md:hidden">
          {nav.map(({ to, label }) => (
            <Link key={to} to={to} activeOptions={{ exact: to === "/" }} className="whitespace-nowrap rounded px-3 py-1.5 text-sm text-muted-foreground data-[status=active]:bg-ink data-[status=active]:text-ink-foreground">
              {label}
            </Link>
          ))}
        </nav>
        <main className="mx-auto w-full max-w-6xl flex-1 px-5 py-8 md:px-10 md:py-10">{children}</main>
      </div>
    </div>
  );
}

export function PageHeader({ eyebrow, title, children }: { eyebrow?: string; title: ReactNode; children?: ReactNode }) {
  return (
    <header className="mb-8 flex flex-wrap items-end justify-between gap-4 border-b pb-6">
      <div>
        {eyebrow && <div className="mb-2 text-xs uppercase tracking-[0.2em] text-muted-foreground">{eyebrow}</div>}
        <h1 className="font-display text-4xl leading-tight md:text-5xl">{title}</h1>
      </div>
      {children && <div className="flex gap-2">{children}</div>}
    </header>
  );
}
