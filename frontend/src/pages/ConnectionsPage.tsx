import { useState, useEffect } from "react";
import { Landmark, Mail, RefreshCw, ShieldCheck, Trash2, Unlink, CheckCircle2, Upload, FileText } from "lucide-react";
import { toast } from "sonner";
import { PageHeader } from "@/components/app/AppShell";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { DeleteDataDialog } from "@/components/connections/DeleteDataDialog";
import { apiClient } from "@/services/apiClient";
import type { Connection } from "@/types";

export function ConnectionsPage() {
  const [connections, setConnections] = useState<Connection[]>([]);
  const [syncingId, setSyncingId] = useState<string | null>(null);
  const [syncProgress, setSyncProgress] = useState(0);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [uploading, setUploading] = useState(false);

  const fetchConnections = async () => {
    const conns = await apiClient.getConnections();
    setConnections(conns);
  };

  useEffect(() => {
    fetchConnections();
  }, []);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const result = await apiClient.uploadCsvStatement(formData);
      toast.success("CSV Statement Ingested", {
        description: `Imported ${result.importedTransactions} transactions and detected ${result.detectedSubscriptions} subscriptions.`,
      });
      await fetchConnections();
    } catch {
      toast.error("Failed to upload statement CSV");
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  };

  const handleSync = async (id: string) => {
    setSyncingId(id);
    setSyncProgress(25);

    const timer1 = setTimeout(() => setSyncProgress(65), 300);
    const timer2 = setTimeout(() => setSyncProgress(95), 600);

    try {
      const updated = await apiClient.triggerSync(id);
      setSyncProgress(100);
      setConnections((prev) => prev.map((c) => (c.id === id ? updated : c)));
      toast.success("Synchronization Complete", {
        description: `Imported newest transactions and invoice receipts for ${updated.name}.`,
      });
    } catch {
      toast.error("Failed to sync connection");
    } finally {
      setTimeout(() => {
        setSyncingId(null);
        setSyncProgress(0);
      }, 500);
      clearTimeout(timer1);
      clearTimeout(timer2);
    }
  };

  const handleDisconnect = async (id: string) => {
    await apiClient.disconnectConnection(id);
    setConnections((prev) =>
      prev.map((c) => (c.id === id ? { ...c, status: "disconnected" as const } : c))
    );
    toast.info("Connection Disconnected", {
      description: "Data sync has been paused and linked pending findings removed.",
    });
  };

  const handleDeleteAllData = async () => {
    await apiClient.deleteUserData();
    await fetchConnections();
    toast.success("All Imported Data Purged", {
      description: "Stored transactions, email snippets, and findings completely erased.",
    });
  };

  return (
    <div className="space-y-8">
      <PageHeader eyebrow="Integrations & Privacy" title="Connections">
        <Button
          variant="destructive"
          size="sm"
          className="gap-1.5 text-xs"
          onClick={() => setDeleteDialogOpen(true)}
        >
          <Trash2 className="size-3.5" />
          Delete All Imported Data
        </Button>
      </PageHeader>

      <p className="-mt-4 text-sm text-muted-foreground max-w-3xl">
        Manage read-only connections to your business financial feeds and Google Workspace invoice receipts.
        All data is processed strictly locally with zero external tracking.
      </p>

      {/* Connection Cards */}
      <div className="grid gap-6 md:grid-cols-2">
        {connections.map((c) => {
          const isSyncing = syncingId === c.id;
          const isConnected = c.status === "connected";

          return (
            <Card key={c.id} className="flex flex-col justify-between border bg-card">
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className="rounded-lg bg-muted p-2.5">
                      {c.type === "bank" ? <Landmark className="size-6 text-foreground" /> : <Mail className="size-6 text-foreground" />}
                    </div>
                    <div>
                      <CardTitle className="text-base font-bold">{c.name}</CardTitle>
                      <div className="text-xs text-muted-foreground capitalize">
                        {c.provider} · {c.accountMask || c.emailAddress || "Synthetic Integration"}
                      </div>
                    </div>
                  </div>
                  <Badge
                    variant="outline"
                    className={
                      isConnected
                        ? "border-emerald-500/40 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400"
                        : "border-muted text-muted-foreground"
                    }
                  >
                    {isConnected ? "Connected" : "Disconnected"}
                  </Badge>
                </div>
              </CardHeader>

              <CardContent className="space-y-4 text-xs">
                <div className="grid grid-cols-2 gap-2 rounded-lg bg-muted/30 p-3">
                  <div>
                    <span className="text-muted-foreground">Last Successful Sync:</span>
                    <div className="font-medium text-foreground mt-0.5">
                      {new Date(c.lastSyncedAt).toLocaleString([], { dateStyle: "medium", timeStyle: "short" })}
                    </div>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Permission Scopes:</span>
                    <div className="font-mono text-foreground mt-0.5">
                      {c.type === "bank" ? "transactions:read, accounts:read" : "gmail.readonly (receipts only)"}
                    </div>
                  </div>
                </div>

                {isSyncing && (
                  <div className="space-y-1.5 pt-1">
                    <div className="flex justify-between text-[11px] text-muted-foreground">
                      <span>Syncing synthetic feed...</span>
                      <span>{syncProgress}%</span>
                    </div>
                    <Progress value={syncProgress} className="h-1.5" />
                  </div>
                )}
              </CardContent>

              <CardFooter className="flex items-center justify-between border-t bg-muted/10 pt-3">
                <Button
                  size="sm"
                  variant="outline"
                  className="h-8 gap-1.5 text-xs"
                  disabled={!isConnected || isSyncing}
                  onClick={() => handleSync(c.id)}
                >
                  <RefreshCw className={`size-3.5 ${isSyncing ? "animate-spin" : ""}`} />
                  {isSyncing ? "Syncing..." : "Sync Now"}
                </Button>

                {isConnected ? (
                  <Button
                    size="sm"
                    variant="ghost"
                    className="h-8 gap-1.5 text-xs text-destructive hover:bg-destructive/10"
                    onClick={() => handleDisconnect(c.id)}
                  >
                    <Unlink className="size-3.5" />
                    Disconnect
                  </Button>
                ) : (
                  <Button
                    size="sm"
                    variant="outline"
                    className="h-8 gap-1.5 text-xs"
                    onClick={() => handleSync(c.id)}
                  >
                    Reconnect
                  </Button>
                )}
              </CardFooter>
            </Card>
          );
        })}
      </div>

      {/* Manual CSV Statement Import */}
      <Card className="border border-border/80">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-base font-semibold">
            <FileText className="size-5 text-primary" />
            Manual Bank Statement CSV Upload
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <p className="text-xs text-muted-foreground">
            Import bank statement CSV files directly to discover subscriptions without connecting an external bank account. Date, Merchant, and Amount columns are automatically detected.
          </p>
          <div className="flex flex-wrap items-center gap-3 pt-1">
            <label className="cursor-pointer">
              <input
                type="file"
                accept=".csv"
                className="hidden"
                onChange={handleFileUpload}
                disabled={uploading}
              />
              <Button variant="outline" size="sm" className="gap-2 text-xs" asChild disabled={uploading}>
                <span>
                  <Upload className={`size-3.5 ${uploading ? "animate-spin" : ""}`} />
                  {uploading ? "Importing Statement..." : "Select CSV Statement"}
                </span>
              </Button>
            </label>
            <span className="text-[11px] text-muted-foreground">
              Accepts .csv files (Chase, Mercury, Silicon Valley Bank, Brex, etc.)
            </span>
          </div>
        </CardContent>
      </Card>

      {/* Clear Privacy Disclosures */}
      <Card className="border border-border/80 bg-muted/20">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-base font-semibold">
            <ShieldCheck className="size-5 text-emerald-600 dark:text-emerald-400" />
            Data Privacy & Security Commitments
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-xs leading-relaxed text-muted-foreground">
          <p>
            <strong>Read-Only Access:</strong> SubTracker cannot initiate payments, move funds, or send emails. We only read payment descriptors and vendor invoice confirmations.
          </p>
          <p>
            <strong>Local SQLite Database:</strong> All parsed transactions, subscriptions, and review decisions reside locally within your local SQLite database (`app.db` / `subtracker.db`). Zero data is uploaded to external analytics or advertising brokers.
          </p>
          <p>
            <strong>Strict Data Retention & Purge:</strong> When you click "Delete All Imported Data", every imported transaction and finding is irreversibly removed from storage immediately.
          </p>
        </CardContent>
      </Card>

      <DeleteDataDialog
        open={deleteDialogOpen}
        onOpenChange={setDeleteDialogOpen}
        onConfirm={handleDeleteAllData}
      />
    </div>
  );
}
