import { useState } from "react";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onConfirm: () => void;
}

export function DeleteDataDialog({ open, onOpenChange, onConfirm }: Props) {
  const [confirmText, setConfirmText] = useState("");

  const handleConfirm = () => {
    if (confirmText.toLowerCase() === "delete") {
      onConfirm();
      setConfirmText("");
      onOpenChange(false);
    }
  };

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle className="text-destructive font-bold">
            Permanently Delete All Imported Data?
          </AlertDialogTitle>
          <AlertDialogDescription className="space-y-2 text-sm">
            <span>
              This will permanently purge all imported bank transactions, extracted email receipts,
              detected subscriptions, and review findings from local storage. This action cannot be undone.
            </span>
          </AlertDialogDescription>
        </AlertDialogHeader>

        <div className="space-y-2 py-2">
          <Label htmlFor="delete-confirm" className="text-xs font-medium">
            Type <strong className="text-foreground">DELETE</strong> to confirm:
          </Label>
          <Input
            id="delete-confirm"
            value={confirmText}
            onChange={(e) => setConfirmText(e.target.value)}
            placeholder="DELETE"
            className="font-mono text-sm"
          />
        </div>

        <AlertDialogFooter>
          <AlertDialogCancel onClick={() => setConfirmText("")}>Cancel</AlertDialogCancel>
          <AlertDialogAction
            onClick={handleConfirm}
            disabled={confirmText.toLowerCase() !== "delete"}
            className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
          >
            Permanently Purge Data
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
