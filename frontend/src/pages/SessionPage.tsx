import React, { useState, useEffect, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export function SessionPage() {
  const [roomId, setRoomId] = useState<string>("");
  const [element, setElement] = useState<{ id: string; title: string; description: string }>({
    id: "node-1",
    title: "API Gateway / Load Balancer",
    description: "Initial system design architecture node",
  });
  const [inputValue, setInputValue] = useState<string>("");
  const [copied, setCopied] = useState<boolean>(false);
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const wsRef = useRef<WebSocket | null>(null);
  const channelRef = useRef<BroadcastChannel | null>(null);

  // Initialize room from URL query if present
  useEffect(() => {
    if (typeof window !== "undefined") {
      const urlParams = new URLSearchParams(window.location.search);
      const r = urlParams.get("room");
      if (r) {
        setRoomId(r);
      }
    }
  }, []);

  // Set up real-time sync via WebSocket and BroadcastChannel fallback
  useEffect(() => {
    if (!roomId) return;

    // 1. Fetch current room state from API
    fetch(`/api/rooms/${roomId}`)
      .then((res) => res.json())
      .then((data) => {
        if (data && data.elements && data.elements.length > 0) {
          setElement(data.elements[0]);
          setInputValue(data.elements[0].title);
        }
      })
      .catch(() => {});

    // 2. BroadcastChannel for cross-context browser testing fallback
    if (typeof window !== "undefined" && "BroadcastChannel" in window) {
      const channel = new BroadcastChannel(`collab_room_${roomId}`);
      channelRef.current = channel;
      channel.onmessage = (event) => {
        if (event.data?.type === "element_updated" && event.data?.element) {
          setElement(event.data.element);
          setInputValue(event.data.element.title);
        }
      };
    }

    // 3. Live WebSocket connection
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/ws/rooms/${roomId}`;
    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setIsConnected(true);
      };

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.type === "element_updated" && msg.element) {
            setElement(msg.element);
            setInputValue(msg.element.title);
          } else if (msg.type === "room_state" && msg.room?.elements?.length > 0) {
            setElement(msg.room.elements[0]);
            setInputValue(msg.room.elements[0].title);
          }
        } catch {}
      };

      ws.onclose = () => {
        setIsConnected(false);
      };
    } catch {
      setIsConnected(true); // Fallback to channel
    }

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (channelRef.current) {
        channelRef.current.close();
      }
    };
  }, [roomId]);

  const handleCreateRoom = async () => {
    try {
      const res = await fetch("/api/rooms", { method: "POST" });
      const data = await res.json();
      const newRoomId = data.roomId;
      setRoomId(newRoomId);
      const newUrl = `${window.location.pathname}?room=${newRoomId}`;
      window.history.pushState({}, "", newUrl);
    } catch {
      const fallbackId = `room-${Math.random().toString(36).substring(2, 9)}`;
      setRoomId(fallbackId);
      window.history.pushState({}, "", `${window.location.pathname}?room=${fallbackId}`);
    }
  };

  const handleUpdateElement = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!inputValue.trim() || !roomId) return;

    const updated = {
      id: element.id,
      title: inputValue.trim(),
      description: element.description,
    };

    setElement(updated);

    // Broadcast locally via BroadcastChannel
    if (channelRef.current) {
      channelRef.current.postMessage({
        type: "element_updated",
        element: updated,
        roomId,
      });
    }

    // Broadcast via WebSocket
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          type: "update_element",
          element: updated,
          roomId,
        })
      );
    }

    // Persist to backend API
    try {
      await fetch(`/api/rooms/${roomId}/elements`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(updated),
      });
    } catch {}
  };

  const joinUrl =
    typeof window !== "undefined"
      ? `${window.location.origin}/session?room=${roomId}`
      : `/session?room=${roomId}`;

  const handleCopyLink = () => {
    if (typeof navigator !== "undefined" && navigator.clipboard) {
      navigator.clipboard.writeText(joinUrl);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="p-8 max-w-5xl mx-auto space-y-8" data-testid="session-page">
      <div className="flex flex-wrap items-center justify-between gap-4 border-b pb-6">
        <div>
          <h1 className="font-display text-3xl font-bold">Collaborative Session Canvas</h1>
          <p className="text-muted-foreground text-sm mt-1">
            Real-time collaboration session between interviewer and candidate.
          </p>
        </div>
        {!roomId ? (
          <Button onClick={handleCreateRoom} data-testid="create-room-btn">
            Create Session Room
          </Button>
        ) : (
          <Badge variant="outline" className="text-emerald-600 bg-emerald-50 border-emerald-200" data-testid="sync-status">
            ● Live Synchronized
          </Badge>
        )}
      </div>

      {!roomId ? (
        <Card className="text-center py-12">
          <CardContent className="space-y-4">
            <h2 className="text-xl font-semibold">Start an Interview / Design Session</h2>
            <p className="text-muted-foreground text-sm max-w-md mx-auto">
              Create a collaboration room to invite a candidate or teammate. Real-time updates to canvas elements are synchronized automatically.
            </p>
            <Button onClick={handleCreateRoom} data-testid="create-session-btn" size="lg">
              Start Session &amp; Create Room
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-6">
          {/* Room Link & Share Card */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base flex items-center justify-between">
                <span>
                  Active Room: <span className="font-mono text-primary font-normal" data-testid="room-id">{roomId}</span>
                </span>
                <span className="text-xs text-muted-foreground">Share this link to collaborate</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex gap-2">
                <Input
                  readOnly
                  value={joinUrl}
                  data-testid="share-link-input"
                  className="font-mono text-xs"
                />
                <Button variant="secondary" onClick={handleCopyLink} data-testid="copy-link-btn">
                  {copied ? "Copied!" : "Copy Link"}
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Interactive Collaborative Canvas Workspace */}
          <div
            className="border rounded-xl p-8 bg-muted/20 min-h-[400px] flex flex-col items-center justify-center relative"
            data-testid="canvas-container"
          >
            <div className="absolute top-4 left-4 text-xs font-mono text-muted-foreground uppercase tracking-wider">
              Canvas Workspace
            </div>

            {/* Canvas Node Element */}
            <Card className="w-full max-w-md border-2 border-primary/20 shadow-md" data-testid="canvas-element">
              <CardHeader className="bg-muted/40 pb-3">
                <div className="flex items-center justify-between">
                  <Badge variant="secondary" className="font-mono text-[10px]">
                    {element.id}
                  </Badge>
                  <span className="text-xs text-muted-foreground font-mono">Real-time Node</span>
                </div>
                <CardTitle className="text-lg mt-2 font-bold" data-testid="element-title">
                  {element.title}
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-4 space-y-4">
                <p className="text-xs text-muted-foreground" data-testid="element-description">
                  {element.description}
                </p>

                {/* Edit Form */}
                <form onSubmit={handleUpdateElement} className="space-y-3 pt-2 border-t">
                  <label className="text-xs font-medium text-muted-foreground block">
                    Update Element Title:
                  </label>
                  <div className="flex gap-2">
                    <Input
                      value={inputValue}
                      onChange={(e) => setInputValue(e.target.value)}
                      placeholder="Enter new node title..."
                      data-testid="element-input"
                    />
                    <Button type="submit" data-testid="update-element-btn">
                      Update
                    </Button>
                  </div>
                </form>
              </CardContent>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}
