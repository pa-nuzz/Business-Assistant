"use client";

import { useState, useEffect } from "react";
import { user, type Session } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { toast } from "sonner";
import { 
  Monitor, 
  Smartphone, 
  Tablet, 
  Trash2, 
  LogOut,
  AlertTriangle,
  CheckCircle2,
  Loader2
} from "lucide-react";

interface SessionManagementProps {
  onPasswordChanged?: () => void;
}

function formatDate(dateString: string): string {
  if (!dateString) return "Unknown";
  const date = new Date(dateString);
  return date.toLocaleDateString(undefined, { 
    month: "short", 
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit"
  });
}

function getDeviceIcon() {
  // Could be enhanced with user agent parsing
  return Monitor;
}

export function SessionManagement({ onPasswordChanged }: SessionManagementProps) {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [revokingSession, setRevokingSession] = useState<string | null>(null);
  const [isRevokingAll, setIsRevokingAll] = useState(false);

  const loadSessions = async () => {
    try {
      const data = await user.listSessions();
      setSessions(data.sessions || []);
    } catch (error) {
      toast.error("Failed to load active sessions");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadSessions();
  }, []);

  const handleRevokeSession = async (sessionId: string) => {
    setRevokingSession(sessionId);
    try {
      await user.revokeSession(sessionId);
      toast.success("Session terminated successfully");
      await loadSessions();
    } catch (error) {
      toast.error("Failed to terminate session");
    } finally {
      setRevokingSession(null);
    }
  };

  const handleRevokeAllOthers = async () => {
    setIsRevokingAll(true);
    try {
      const result = await user.revokeAllOtherSessions();
      toast.success(result.message || "All other sessions terminated");
      await loadSessions();
    } catch (error) {
      toast.error("Failed to terminate other sessions");
    } finally {
      setIsRevokingAll(false);
    }
  };

  const activeSessions = sessions.filter(s => s.is_active);
  const otherSessions = activeSessions.filter(s => !s.is_current);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Security Alert */}
      {otherSessions.length > 0 && (
        <div className="flex items-start gap-3 p-4 rounded-lg bg-amber-50 border border-amber-200 dark:bg-amber-950/20 dark:border-amber-900/50">
          <AlertTriangle className="h-5 w-5 text-amber-600 mt-0.5 flex-shrink-0" />
          <div>
            <p className="text-sm font-medium text-amber-900 dark:text-amber-100">
              {otherSessions.length} active session{otherSessions.length > 1 ? "s" : ""} on other device{otherSessions.length > 1 ? "s" : ""}
            </p>
            <p className="text-sm text-amber-700 dark:text-amber-200 mt-1">
              If you don&apos;t recognize these sessions, terminate them immediately.
            </p>
          </div>
        </div>
      )}

      {/* Session List */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>Active Sessions</CardTitle>
            <CardDescription>
              Manage your active sessions across devices
            </CardDescription>
          </div>
          {otherSessions.length > 0 && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleRevokeAllOthers}
              disabled={isRevokingAll}
            >
              {isRevokingAll ? (
                <Loader2 className="h-4 w-4 animate-spin mr-2" />
              ) : (
                <LogOut className="h-4 w-4 mr-2" />
              )}
              End Other Sessions
            </Button>
          )}
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {sessions.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-8">
                No active sessions found
              </p>
            ) : (
              sessions.map((session) => {
                const DeviceIcon = getDeviceIcon();
                return (
                  <div
                    key={session.id}
                    className={`flex items-center justify-between p-4 rounded-lg border ${
                      session.is_current
                        ? "bg-primary/5 border-primary/20"
                        : "bg-card border-border"
                    }`}
                  >
                    <div className="flex items-center gap-4">
                      <div className="h-10 w-10 rounded-full bg-muted flex items-center justify-center">
                        <DeviceIcon className="h-5 w-5 text-muted-foreground" />
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <p className="font-medium text-sm">
                            {session.device_info || "Unknown device"}
                          </p>
                          {session.is_current && (
                            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-primary/10 text-primary">
                              <CheckCircle2 className="h-3 w-3 mr-1" />
                              Current
                            </span>
                          )}
                          {!session.is_active && (
                            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-muted text-muted-foreground">
                              Terminated
                            </span>
                          )}
                        </div>
                        <div className="flex items-center gap-3 text-sm text-muted-foreground mt-1">
                          <span>IP: {session.ip_address || "Unknown"}</span>
                          <span>•</span>
                          <span>Started: {formatDate(session.created_at)}</span>
                          {session.expires_at && (
                            <>
                              <span>•</span>
                              <span>Expires: {formatDate(session.expires_at)}</span>
                            </>
                          )}
                        </div>
                      </div>
                    </div>
                    {!session.is_current && session.is_active && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleRevokeSession(session.id)}
                        disabled={revokingSession === session.id}
                        className="text-destructive hover:text-destructive hover:bg-destructive/10"
                      >
                        {revokingSession === session.id ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <Trash2 className="h-4 w-4" />
                        )}
                      </Button>
                    )}
                  </div>
                );
              })
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
