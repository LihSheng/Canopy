"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { ErrorState } from "@/components/shared/error-state";
import { EmptyState } from "@/components/shared/empty-state";
import { StaleIndicator } from "@/components/shared/stale-indicator";
import { formatPercent, getSeverityColor } from "@/lib/formatters";
import { fetchAnomalies } from "@/lib/api/dashboard";
import type { Anomaly } from "@/lib/api/types";

type DataState =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "success"; anomalies: Anomaly[] };

export function AnomaliesShell() {
  const [data, setData] = useState<DataState>({ status: "loading" });

  const load = useCallback(async () => {
    setData({ status: "loading" });
    try {
      const anomalies = await fetchAnomalies();
      setData({ status: "success", anomalies });
    } catch (err) {
      setData({
        status: "error",
        message: err instanceof Error ? err.message : "Failed to load anomalies",
      });
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- initial data fetch
    load();
  }, [load]);

  if (data.status === "error") {
    return <ErrorState message={data.message} onRetry={load} />;
  }

  const loading = data.status === "loading";

  return (
    <div className="space-y-6">
      <div>
        <Link
          href="/dashboard"
          className="mb-2 inline-flex text-sm font-medium text-zinc-500 hover:text-zinc-900 transition-colors"
        >
          &larr; Back to Dashboard
        </Link>
        <h1 className="text-2xl font-semibold tracking-tight text-zinc-900">
          Anomalies
        </h1>
        <StaleIndicator
          lastUpdated={
            data.status === "success" && data.anomalies.length > 0
              ? data.anomalies[0].period
              : undefined
          }
        />
      </div>

      {loading && (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-20 animate-pulse rounded-xl bg-zinc-50" />
          ))}
        </div>
      )}

      {data.status === "success" && data.anomalies.length === 0 && (
        <EmptyState
          title="No anomalies detected"
          description="All departments are within expected spend ranges."
        />
      )}

      {data.status === "success" && data.anomalies.length > 0 && (
        <div className="space-y-3">
          {data.anomalies.map((a) => (
            <div
              key={a.id}
              className="rounded-xl border border-zinc-200 bg-white p-5"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <Link
                      href={`/dashboard/departments/${a.department_id}`}
                      className="text-sm font-semibold text-zinc-900 hover:text-zinc-600 transition-colors"
                    >
                      {a.department_name}
                    </Link>
                    <span className="text-xs text-zinc-400">{a.period}</span>
                  </div>
                  <p className="mt-1 text-sm text-zinc-600">{a.description}</p>
                </div>
                <div className="flex shrink-0 items-center gap-3">
                  <span className={`inline-flex rounded-full border px-2.5 py-0.5 text-xs font-medium ${getSeverityColor(a.severity)}`}>
                    {a.severity}
                  </span>
                  {a.change_pct !== 0 && (
                    <span
                      className={`text-sm font-semibold tabular-nums ${
                        a.change_pct > 0 ? "text-red-600" : "text-emerald-600"
                      }`}
                    >
                      {formatPercent(a.change_pct)}
                    </span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
