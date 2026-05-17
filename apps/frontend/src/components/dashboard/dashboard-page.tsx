"use client";

import { useCallback, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { AnalyticsHeader } from "@/components/analytics-shell/analytics-header";
import { ErrorState } from "@/components/shared/error-state";
import { EmptyState } from "@/components/shared/empty-state";
import { ManualRefreshButton, RefreshTimelinePanel, useRefreshPoller } from "@/components/dashboard/refresh-widgets";
import { DashboardSummaryGrid, DashboardSummaryGridSkeleton } from "./dashboard-summary-grid";
import { DashboardAttentionPanel, DashboardAttentionPanelSkeleton } from "./dashboard-attention-panel";
import { DashboardAiSummaryPanel, DashboardAiSummaryPanelSkeleton } from "./dashboard-ai-summary-panel";
import { DashboardTrendPanel, DashboardTrendPanelSkeleton } from "./dashboard-trend-panel";
import { DashboardDepartmentPreview, DashboardDepartmentPreviewSkeleton } from "./dashboard-department-preview";
import {
  fetchSummary,
  fetchDepartments,
  fetchMonthlyTrends,
  fetchClaimTypeBreakdown,
  fetchAnomalies,
} from "@/lib/api/dashboard";
import { mapCommandView } from "./dashboard-mappers";
import { readDashboardState } from "@/lib/navigation/route-state";
import { TIME_RANGE_LABELS } from "@/lib/navigation/time-range";
import type { DashboardCommandView } from "./dashboard-mappers";

type DataState =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "success"; view: DashboardCommandView };

export function DashboardPage() {
  const searchParams = useSearchParams();
  const { timeRange } = readDashboardState(searchParams);
  const { status: refreshStatus } = useRefreshPoller();

  const [data, setData] = useState<DataState>({ status: "loading" });

  const load = useCallback(async () => {
    setData({ status: "loading" });
    try {
      const [summary, departments, trends, claimTypes, anomalies] = await Promise.all([
        fetchSummary(),
        fetchDepartments(),
        fetchMonthlyTrends(),
        fetchClaimTypeBreakdown(),
        fetchAnomalies(),
      ]);
      const view = mapCommandView(summary, departments, trends, claimTypes, anomalies, timeRange);
      setData({ status: "success", view });
    } catch (err) {
      setData({
        status: "error",
        message: err instanceof Error ? err.message : "Failed to load dashboard",
      });
    }
  }, [timeRange]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- initial data fetch
    load();
  }, [load]);

  const contextLabel = TIME_RANGE_LABELS[timeRange];

  if (data.status === "error") {
    return (
      <>
        <AnalyticsHeader title="Dashboard" contextText={contextLabel} />
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
        title="Dashboard"
        contextText={
          loading
            ? undefined
            : data.status === "success"
              ? `${contextLabel} \u00b7 Snapshot ${data.view.snapshotLabel}`
              : contextLabel
        }
        actions={
          <div className="flex items-center gap-3">
            <span className="text-xs text-zinc-400">{TIME_RANGE_LABELS[timeRange]}</span>
            <ManualRefreshButton />
          </div>
        }
      />

      <div className="flex-1 overflow-auto p-6">
        {refreshStatus && refreshStatus.last_refresh && (
          <RefreshTimelinePanel
            lastRefresh={refreshStatus.last_refresh}
            lastAttempt={refreshStatus.last_attempt}
          />
        )}

        {data.status === "success" &&
        data.view.summaryCards.totalSpend.value === 0 &&
        data.view.topDepartments.length === 0 ? (
          <EmptyState
            title="No dashboard data"
            description="Data will appear after the first sync completes. Try refreshing."
          />
        ) : (
          <div className="space-y-6">
            {/* First band: attention panel + summary grid */}
            <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
              <div className="lg:col-span-2">
                {loading ? (
                  <DashboardAttentionPanelSkeleton />
                ) : data.status === "success" ? (
                  <DashboardAttentionPanel
                    items={data.view.topAttentionItems}
                    timeRange={timeRange}
                  />
                ) : null}
              </div>
              <div className="lg:col-span-1">
                {loading ? (
                  <DashboardSummaryGridSkeleton />
                ) : data.status === "success" ? (
                  <DashboardSummaryGrid
                    cards={data.view.summaryCards}
                    timeRange={timeRange}
                  />
                ) : null}
              </div>
            </div>

            {/* Second band: AI summary + trend chart */}
            <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
              <div className="lg:col-span-1">
                {loading ? (
                  <DashboardAiSummaryPanelSkeleton />
                ) : data.status === "success" ? (
                  <DashboardAiSummaryPanel summary={data.view.aiSummary} />
                ) : null}
              </div>
              <div className="lg:col-span-2">
                {loading ? (
                  <DashboardTrendPanelSkeleton />
                ) : data.status === "success" ? (
                  <DashboardTrendPanel series={data.view.trendSeries} />
                ) : null}
              </div>
            </div>

            {/* Third band: top 5 department preview */}
            <div>
              {loading ? (
                <DashboardDepartmentPreviewSkeleton />
              ) : data.status === "success" ? (
                <DashboardDepartmentPreview
                  departments={data.view.topDepartments}
                  timeRange={timeRange}
                />
              ) : null}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
