import type { BillingInterval, Money } from "./api/types";

const FACTORS: Record<BillingInterval, number> = {
  weekly: 52 / 12,
  monthly: 1,
  quarterly: 1 / 3,
  annual: 1 / 12,
  irregular: 1,
  unknown: 1,
};

/** Normalize a recurring amount (minor units) to a monthly equivalent, rounded to the nearest minor unit. */
export function monthlyEquivalentMinor(amountMinor: number, interval: BillingInterval): number {
  return Math.round(amountMinor * FACTORS[interval]);
}

function minorDigits(currency: string) {
  return new Intl.NumberFormat("en", { style: "currency", currency }).resolvedOptions().maximumFractionDigits ?? 2;
}

export function toMinor(major: string, currency: string): number {
  const d = minorDigits(currency);
  const [i, f = ""] = major.trim().replace(/,/g, "").split(".");
  return Number(i || "0") * 10 ** d + Number((f + "0".repeat(d)).slice(0, d) || "0") * ((i ?? "").startsWith("-") ? -1 : 1);
}

export function formatMoney(m: Money | null | undefined, opts: { abs?: boolean } = {}): string {
  if (!m) return "—";
  const d = minorDigits(m.currency);
  const v = (opts.abs ? Math.abs(m.amountMinor) : m.amountMinor) / 10 ** d;
  return new Intl.NumberFormat(undefined, { style: "currency", currency: m.currency }).format(v);
}

export function formatDate(iso: string | null | undefined, opts: Intl.DateTimeFormatOptions = { month: "short", day: "numeric", year: "numeric" }) {
  if (!iso) return "—";
  return new Intl.DateTimeFormat(undefined, opts).format(new Date(iso));
}

export function relativeDays(iso: string) {
  const days = Math.round((new Date(iso).getTime() - Date.now()) / 864e5);
  return new Intl.RelativeTimeFormat(undefined, { numeric: "auto" }).format(days, "day");
}
