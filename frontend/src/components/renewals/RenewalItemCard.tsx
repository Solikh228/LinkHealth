import { Link } from "@tanstack/react-router";
import { Bell, Calendar, ChevronRight, Tag } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import type { Renewal } from "@/types";

interface Props {
  renewal: Renewal;
  onToggleReminder: (id: string) => void;
}

export function RenewalItemCard({ renewal, onToggleReminder }: Props) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 rounded-lg border bg-card transition hover:border-foreground/30">
      <Link
        to="/subscriptions"
        className="flex-1 flex items-start gap-3.5 group"
      >
        <div className="rounded-lg bg-muted p-2.5 mt-0.5 text-muted-foreground group-hover:text-foreground">
          <Calendar className="size-5" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="font-bold text-base text-foreground group-hover:underline">
              {renewal.vendorName}
            </span>
            <Badge variant="outline" className="text-[10px] uppercase">
              {renewal.cadence}
            </Badge>
          </div>
          <div className="flex items-center gap-2 mt-1 text-xs text-muted-foreground">
            <span>Due on {renewal.dueDate}</span>
            <span>•</span>
            <span className="flex items-center gap-1 text-emerald-600 dark:text-emerald-400">
              <Tag className="size-3" />
              {renewal.evidenceTag}
            </span>
          </div>
        </div>
      </Link>

      <div className="flex items-center justify-between sm:justify-end gap-5 border-t sm:border-t-0 pt-2 sm:pt-0">
        <div className="text-right">
          <div className="font-bold text-base text-foreground">
            ${(renewal.amount.amountMinor / 100).toFixed(2)}
          </div>
          <div className="text-[11px] text-muted-foreground capitalize">
            {renewal.cadence} renewal
          </div>
        </div>

        <div className="flex items-center gap-2 pl-3 border-l">
          <label htmlFor={`remind-${renewal.id}`} className="text-xs text-muted-foreground cursor-pointer flex items-center gap-1">
            <Bell className={`size-3.5 ${renewal.hasReminder ? "text-amber-500 fill-amber-500" : ""}`} />
            <span className="hidden md:inline">Priority Reminder</span>
          </label>
          <Switch
            id={`remind-${renewal.id}`}
            checked={renewal.hasReminder}
            onCheckedChange={() => onToggleReminder(renewal.id)}
          />
        </div>
      </div>
    </div>
  );
}
