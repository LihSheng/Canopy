"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { fetchRefreshStatus, triggerRefresh } from "@/lib/api/dashboard";
import type { RefreshStatus } from "@/lib/api/types";

export function RefreshStatusBadge({ status }: { status: RefreshStatus["status"] }) {
  const labels: Record<RefreshStatus["status"], { text: string; className: string }> = {
    idle: { text: "Up to date", className: "bg-emerald-50 text-emerald-700" },
    queued: { text: "Queued", className: "bg-blue-50 text-blue-700" },
    running: { text: "Refreshing...", className: "bg-amber-50 text-amber-700" },
    completed: { text: "Completed", className: "bg-emerald-50 text-emerald-700" },
    failed: { text: "Failed", className: "bg-red-50 text-red-700" },
  };

  const info = labels[status] ?? labels.idle;

  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium ${info.className}`}>
      {status === "running" && (
        <svg className="h-3 w-3 animate-spin" viewBox="0 0 12 12" fill="none">
          <circle cx="6" cy="6" r="5" stroke="currentColor" strokeWidth="2" className="opacity-25" />
          <path d="M6 1a5 5 0 015 5" stroke="currentColor" strokeWidth="2" className="opacity-75" />
        </svg>
      )}
      {info.text}
    </span>
  );
}

export function ManualRefreshButton() {
  const [loading, setLoading] = useState(false);

  const handleRefresh = useCallback(async () => {
    setLoading(true);
    try {
      await triggerRefresh();
    } catch {
      // silently fail, status polling will reflect
    } finally {
      setLoading(false);
    }
  }, []);

  return (
    <button
      onClick={handleRefresh}
      disabled={loading}
      className="flex h-9 items-center gap-2 rounded-lg border border-zinc-200 bg-white px-3 text-sm font-medium text-zinc-700 transition-colors hover:bg-zinc-50 disabled:opacity-50"
    >
      <svg
        className={`h-4 w-4 ${loading ? "animate-spin" : ""}`}
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 16 16"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
      >
        <path d="M2 8a6 6 0 0111.3-3.3M14 8a6 6 0 01-11.3 3.3" />
        <path d="M13.5 2v3h-3M2.5 14v-3h3" />
      </svg>
      {loading ? "Refreshing..." : "Refresh data"}
    </button>
  );
}

export function RefreshTimelinePanel({
  lastRefresh,
  lastAttempt,
}: {
  lastRefresh: string | null;
  lastAttempt: string | null;
}) {
  const formatDate = (d: string | null) => {
    if (!d) return "N/A";
    return new Date(d).toLocaleString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <div className="rounded-lg border border-zinc-200 bg-zinc-50 px-4 py-3">
      <div className="flex items-center gap-4 text-xs text-zinc-500">
        <span>
          Last refresh:{" "}
          <span className="font-medium text-zinc-700">{formatDate(lastRefresh)}</span>
        </span>
        {lastAttempt && lastAttempt !== lastRefresh && (
          <span>
            Last attempt:{" "}
            <span className="font-medium text-zinc-700">{formatDate(lastAttempt)}</span>
          </span>
        )}
      </div>
    </div>
  );
}

export function useRefreshPoller(pollMs = 30000) {
  const [status, setStatus] = useState<RefreshStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const check = useCallback(async () => {
    try {
      const s = await fetchRefreshStatus();
      setStatus(s);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Status check failed");
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- initial status fetch + polling
    check();
    intervalRef.current = setInterval(check, pollMs);
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [check, pollMs]);

  return { status, error };
}
