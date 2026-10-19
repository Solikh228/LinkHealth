import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { API_MODE, api, tokenStore } from "@/lib/api/client";

export const Route = createFileRoute("/login")({
  head: () => ({
    meta: [
      { title: "Sign in — Ledgerline" },
      { name: "description", content: "Sign in to find hidden B2B subscriptions and auto-charges." },
      { property: "og:title", content: "Sign in — Ledgerline" },
      { property: "og:description", content: "Find hidden B2B subscriptions and auto-charges." },
    ],
  }),
  component: Login,
});

function Login() {
  const nav = useNavigate();
  const [email, setEmail] = useState(API_MODE === "mock" ? "alex@studio.dev" : "");
  const [password, setPassword] = useState(API_MODE === "mock" ? "demo" : "");
  const m = useMutation({
    mutationFn: () => api.createSession(email, password),
    onSuccess: (r) => { tokenStore.set(r.token); nav({ to: "/" }); },
  });
  return (
    <div className="ledger-rule grid min-h-screen place-items-center px-4">
      <div className="w-full max-w-sm rounded-lg border bg-card p-8 shadow-sm">
        <div className="font-display text-4xl">Ledgerline</div>
        <p className="mt-2 text-sm text-muted-foreground">Find the subscriptions quietly charging your business.</p>
        <form className="mt-8 space-y-3" onSubmit={(e) => { e.preventDefault(); m.mutate(); }}>
          <Input type="email" required placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} />
          <Input type="password" required placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} />
          {m.error && <p className="text-sm text-destructive">{m.error.message}</p>}
          <Button type="submit" className="w-full" disabled={m.isPending}>{m.isPending ? "Signing in…" : "Sign in"}</Button>
        </form>
        {API_MODE === "mock" && <p className="mt-4 text-xs text-muted-foreground">Mock mode: any credentials work.</p>}
      </div>
    </div>
  );
}
