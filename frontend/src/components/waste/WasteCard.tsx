import { Check, X, BellOff, ThumbsUp, Mail, AlertTriangle } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter, CardHeader } from "@/components/ui/card";
import { SeverityDot } from "@/components/app/bits";
import type { Finding, FindingDecision } from "@/types";

interface Props {
  finding: Finding;
  onAction: (findingId: string, decision: FindingDecision) => void;
}

export function WasteCard({ finding, onAction }: Props) {
  const annualSavings = (finding.potentialSavings.amountMinor * 12) / 100;
  const monthlySavings = (finding.potentialSavings.amountMinor / 100).toFixed(2);

  const typeLabels: Record<string, string> = {
    forgotten_charge: "Forgotten Recurring Charge",
    trial_conversion: "Trial Conversion",
    price_increase: "Price Increase",
    duplicate_service: "Possible Duplicate",
    renewal_approaching: "Renewal Approaching",
  };

  return (
    <Card className="flex flex-col justify-between border transition hover:border-foreground/30 bg-card">
      <CardHeader className="space-y-2 pb-3">
        <div className="flex items-center justify-between gap-2">
          <Badge variant="outline" className="text-xs uppercase tracking-wider font-semibold">
            {typeLabels[finding.type] ?? finding.type.replace("_", " ")}
          </Badge>
          <div className="flex items-center gap-1.5 text-xs text-muted-foreground font-mono">
            <SeverityDot s={finding.severity} />
            <span className="capitalize">{finding.severity} priority</span>
          </div>
        </div>
        <div className="text-lg font-bold leading-snug">{finding.title}</div>
        <div className="text-xs font-medium text-muted-foreground">
          Vendor: <span className="text-foreground">{finding.subscriptionName}</span>
        </div>
      </CardHeader>

      <CardContent className="space-y-4 text-sm pb-4">
        {/* Why this may matter hypothesis */}
        <div className="rounded-md bg-muted/40 p-3 text-xs leading-relaxed text-muted-foreground">
          <div className="font-semibold text-foreground mb-1">Why this may matter (Hypothesis):</div>
          {finding.explanation}
        </div>

        {/* Supporting Evidence */}
        <div className="space-y-1.5">
          <div className="text-xs font-semibold text-muted-foreground">Supporting Evidence:</div>
          {finding.evidence.length > 0 ? (
            <div className="space-y-1.5">
              {finding.evidence.map((ev) => (
                <div key={ev.id} className="flex items-start gap-2 rounded border bg-background p-2 text-xs">
                  <Mail className="size-3.5 mt-0.5 text-muted-foreground shrink-0" />
                  <div className="min-w-0 flex-1">
                    <div className="font-medium text-foreground truncate">{ev.subject}</div>
                    <div className="text-[11px] text-muted-foreground italic truncate">"{ev.snippet}"</div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="rounded border border-dashed p-2 text-xs text-muted-foreground">
              Recurring transaction frequency detected without matching email activity.
            </div>
          )}
        </div>

        {/* Confidence & Estimated Savings */}
        <div className="grid grid-cols-2 gap-2 rounded-lg border p-2.5 bg-muted/20 text-xs">
          <div>
            <div className="text-muted-foreground">Confidence Level</div>
            <div className="font-bold text-sm text-foreground">
              {finding.severity === "high" ? "High (94%)" : finding.severity === "medium" ? "Medium (82%)" : "Low (65%)"}
            </div>
          </div>
          <div className="text-right">
            <div className="text-muted-foreground">Estimated Savings</div>
            <div className="font-bold text-sm text-emerald-600 dark:text-emerald-400">
              ${monthlySavings}/mo
            </div>
            <div className="text-[10px] text-muted-foreground">~${annualSavings.toFixed(0)}/yr</div>
          </div>
        </div>
      </CardContent>

      <CardFooter className="flex flex-wrap items-center justify-between gap-1.5 border-t pt-3 bg-muted/10">
        <div className="flex gap-1">
          <Button
            size="sm"
            variant="outline"
            className="h-8 text-xs gap-1 text-emerald-600 hover:text-emerald-700"
            onClick={() => onAction(finding.id, "marked_useful")}
          >
            <ThumbsUp className="size-3" />
            Mark Useful
          </Button>
          <Button
            size="sm"
            variant="ghost"
            className="h-8 text-xs gap-1 text-muted-foreground"
            onClick={() => onAction(finding.id, "snoozed")}
          >
            <BellOff className="size-3" />
            Snooze (30d)
          </Button>
          <Button
            size="sm"
            variant="ghost"
            className="h-8 text-xs gap-1 text-muted-foreground hover:text-foreground"
            onClick={() => onAction(finding.id, "dismissed")}
          >
            <X className="size-3" />
            Dismiss
          </Button>
        </div>

        <Button
          size="sm"
          className="h-8 text-xs gap-1 bg-destructive hover:bg-destructive/90 text-destructive-foreground font-semibold"
          onClick={() => onAction(finding.id, "confirmed_waste")}
        >
          <Check className="size-3" />
          Confirm Waste
        </Button>
      </CardFooter>
    </Card>
  );
}
