"use client";

import { useCallback, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { AnalyticsHeader } from "@/components/analytics-shell/analytics-header";
import { AnalyticsBreadcrumb } from "@/components/analytics-shell/analytics-breadcrumb";
import { ErrorState } from "@/components/shared/error-state";
import { EmptyState } from "@/components/shared/empty-state";
import { AnomaliesGroup } from "./anomalies-group";
import { AnomaliesFilterBar } from "./anomalies-filter-bar";
import { mapAnomalyListView } from "./anomaly-mappers";
import { readAnomalyState } from "@/lib/navigation/route-state";
import { TIME_RANGE_LABELS, type TimeRangeKey } from "@/lib/navigation/time-range";
import { fetchAnomalies } from "@/lib/api/dashboard";
import type { Anomaly } from "@/lib/api/types";
import type { AnomalyListView } from "./anomaly-mappers";

type DataState =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "success"; view: AnomalyListView; allAnomalies: Anomaly[] };

export function AnomaliesPage() {
  const searchParams = useSearchParams();
  const state = readAnomalyState(searchParams);

  const [severityFilter, setSeverityFilter] = useState<"high" | "medium" | "low" | null>(
    state.severity ?? null,
  );
  const [timeRange, setTimeRange] = useState<TimeRangeKey>(state.timeRange);
  const [data, setData] = useState<DataState>({ status: "loading" });

  const load = useCallback(async () => {
    setData({ status: "loading" });
    try {
      const anomalies = await fetchAnomalies();
      const view = mapAnomalyListView(anomalies);
      setData({ status: "success", view, allAnomalies: anomalies });
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

  const contextLabel = TIME_RANGE_LABELS[timeRange];

  if (data.status === "error") {
    return (
      <>
        <AnalyticsHeader title="Anomalies" />
        <AnalyticsBreadcrumb
          items={[
            { label: "Dashboard", href: "/dashboard" },
            { label: "Anomalies" },
          ]}
        />
        <div className="p-6">
          <ErrorState message={data.message} onRetry={load} />
        </div>
      </>
    );
  }

  const loading = data.status === "loading";

  return (
    <div className="flex flex-col h-full overflow-auto">
      <AnalyticsHeader
        title="Anomalies"
        contextText={`${contextLabel}${state.departmentId ? " \u00b7 Filtered by department" : ""}`}
      />
      <AnalyticsBreadcrumb
        items={[
          { label: "Dashboard", href: "/dashboard" },
          { label: "Anomalies" },
        ]}
      />

      <div className="flex-1 overflow-auto p-6">
        <div className="mb-6">
          <AnomaliesFilterBar
            timeRange={timeRange}
            severity={severityFilter}
            departmentId={state.departmentId}
            onTimeRangeChange={setTimeRange}
            onSeverityChange={setSeverityFilter}
          />
        </div>

        {loading && (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="rounded-xl border border-zinc-200 bg-white">
                <div className="flex items-center gap-2.5 px-5 py-3.5">
                  <div className="h-4 w-4 animate-pulse rounded bg-zinc-100" />
                  <div className="h-4 w-28 animate-pulse rounded bg-zinc-100" />
                  <div className="h-5 w-6 animate-pulse rounded-full bg-zinc-100" />
                </div>
              </div>
            ))}
          </div>
        )}

        {data.status === "success" && data.allAnomalies.length === 0 && (
          <EmptyState
            title="No anomalies detected"
            description="All departments are within expected spend ranges for this period."
          />
        )}

        {data.status === "success" && data.allAnomalies.length > 0 && (
          <div className="space-y-3">
            {data.view.groups
              .filter((g) => !severityFilter || g.severity === severityFilter)
              .map((group) => (
                <AnomaliesGroup
                  key={group.severity}
                  group={group}
                  timeRange={timeRange}
                  expandedByDefault={group.severity === "high"}
                />
              ))}
          </div>
        )}
      </div>
    </div>
  );
}
