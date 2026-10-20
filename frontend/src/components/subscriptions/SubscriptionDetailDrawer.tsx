import { useState, useEffect } from "react";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import type { BillingInterval, Subscription } from "@/types";

interface Props {
  subscription: Subscription | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSave: (updated: Subscription) => void;
}

export function SubscriptionDetailDrawer({ subscription, open, onOpenChange, onSave }: Props) {
  const [name, setName] = useState("");
  const [cadence, setCadence] = useState<BillingInterval>("monthly");
  const [status, setStatus] = useState<Subscription["status"]>("active");

  useEffect(() => {
    if (subscription) {
      setName(subscription.name);
      setCadence(subscription.billingInterval);
      setStatus(subscription.status);
    }
  }, [subscription]);

  if (!subscription) return null;

  const handleSave = () => {
    onSave({
      ...subscription,
      name,
      billingInterval: cadence,
      status,
    });
    onOpenChange(false);
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-full sm:max-w-md overflow-y-auto">
        <SheetHeader>
          <SheetTitle className="text-xl font-bold">{subscription.name}</SheetTitle>
          <SheetDescription>Edit subscription details, inspect linked evidence and transactions.</SheetDescription>
        </SheetHeader>

        <div className="mt-6 space-y-6">
          <div className="space-y-4 rounded-lg border p-4 bg-card">
            <h4 className="text-sm font-semibold">Override Subscription Details</h4>
            <div className="space-y-2">
              <Label htmlFor="sub-name" className="text-xs">Display Name</Label>
              <Input id="sub-name" value={name} onChange={(e) => setName(e.target.value)} />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label className="text-xs">Billing Cadence</Label>
                <Select value={cadence} onValueChange={(v) => setCadence(v as BillingInterval)}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="monthly">Monthly</SelectItem>
                    <SelectItem value="annual">Annual</SelectItem>
                    <SelectItem value="quarterly">Quarterly</SelectItem>
                    <SelectItem value="weekly">Weekly</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label className="text-xs">Status</Label>
                <Select value={status} onValueChange={(v) => setStatus(v as Subscription["status"])}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="active">Useful (Active)</SelectItem>
                    <SelectItem value="candidate">Needs Review</SelectItem>
                    <SelectItem value="confirmed">Potential Waste</SelectItem>
                    <SelectItem value="cancelled">Cancelled</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <Button onClick={handleSave} className="w-full" size="sm">Save Changes</Button>
          </div>

          {/* Linked Transactions History */}
          <div className="space-y-3">
            <h4 className="text-sm font-semibold">Linked Transactions History</h4>
            <div className="rounded-lg border divide-y text-xs">
              <div className="p-3 flex justify-between">
                <div>
                  <div className="font-medium">Chase Business Checking</div>
                  <div className="text-muted-foreground">{subscription.lastChargeDate}</div>
                </div>
                <div className="font-semibold text-right">
                  ${(subscription.amount.amountMinor / 100).toFixed(2)}
                  <div className="text-[10px] text-muted-foreground">Posted</div>
                </div>
              </div>
              <div className="p-3 flex justify-between bg-muted/20">
                <div>
                  <div className="font-medium">Prior Statement Charge</div>
                  <div className="text-muted-foreground">30 days earlier</div>
                </div>
                <div className="font-semibold text-right">
                  ${(subscription.amount.amountMinor / 100).toFixed(2)}
                  <div className="text-[10px] text-muted-foreground">Posted</div>
                </div>
              </div>
            </div>
          </div>

          {/* Extracted Email Evidence */}
          <div className="space-y-3">
            <h4 className="text-sm font-semibold">Extracted Email Evidence</h4>
            <div className="rounded-lg border p-3.5 text-xs bg-muted/20 space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-medium text-foreground">{subscription.vendorDomain ?? "vendor.com"}</span>
                <Badge variant="outline" className="text-[10px]">92% confidence</Badge>
              </div>
              <p className="text-muted-foreground italic">
                "{subscription.explanation}"
              </p>
              <div className="text-[11px] text-muted-foreground">
                Matched sender domain and charge date ±24h.
              </div>
            </div>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}
