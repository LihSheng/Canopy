"use client";

import { useCallback, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { TotalPayrollCard } from "./total-payroll-card";
import { TotalClaimsCard } from "./total-claims-card";
import { TopDepartmentsCard } from "./top-departments-card";
import { AnomalyHighlightsCard } from "./anomaly-highlights-card";
import { MonthlyTrendChart } from "./monthly-trend-chart";
import { DepartmentRankingChart } from "./department-ranking-chart";
import { ClaimTypeBreakdownChart } from "./claim-type-breakdown-chart";
import { MonthFilter } from "./month-filter";
import { ManualRefreshButton, RefreshTimelinePanel, useRefreshPoller } from "./refresh-widgets";
import { ErrorState } from "@/components/shared/error-state";
import { StaleIndicator } from "@/components/shared/stale-indicator";
import { EmptyState } from "@/components/shared/empty-state";
import {
  fetchSummary,
  fetchDepartments,
  fetchMonthlyTrends,
  fetchClaimTypeBreakdown,
  fetchAnomalies,
} from "@/lib/api/dashboard";
import { mapToTrendChart } from "@/lib/mappers";
import type {
  DashboardSummary,
  DepartmentSummary,
  MonthlyTrend,
  ClaimTypeBreakdown,
  Anomaly,
} from "@/lib/api/types";

type DataState =
  | { status: "loading" }
  | { status: "error"; message: string }
  | {
      status: "success";
      summary: DashboardSummary;
      departments: DepartmentSummary[];
      trends: MonthlyTrend[];
      claimTypes: ClaimTypeBreakdown[];
      anomalies: Anomaly[];
    };

export function DashboardShell() {
  const searchParams = useSearchParams();
  const year = parseInt(searchParams.get("year") || String(new Date().getFullYear()), 10);
  const month = parseInt(searchParams.get("month") || String(new Date().getMonth() + 1), 10);

  const [data, setData] = useState<DataState>({ status: "loading" });
  const { status: refreshStatus } = useRefreshPoller();

  const load = useCallback(async () => {
    setData({ status: "loading" });
    const params = { year, month };
    try {
      const [summary, departments, trends, claimTypes, anomalies] = await Promise.all([
        fetchSummary(),
        fetchDepartments(params),
        fetchMonthlyTrends(params),
        fetchClaimTypeBreakdown(params),
        fetchAnomalies(),
      ]);
      setData({
        status: "success",
        summary,
        departments,
        trends,
        claimTypes,
        anomalies,
      });
    } catch (err) {
      setData({
        status: "error",
        message: err instanceof Error ? err.message : "Failed to load dashboard",
      });
    }
  }, [year, month]);

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
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-zinc-900">
            Executive Dashboard
          </h1>
          <StaleIndicator lastUpdated={data.status === "success" ? data.summary.last_updated : undefined} />
        </div>
        <div className="flex items-center gap-3">
          <MonthFilter />
          <ManualRefreshButton />
        </div>
      </div>

      {refreshStatus && refreshStatus.last_refresh && (
        <RefreshTimelinePanel
          lastRefresh={refreshStatus.last_refresh}
          lastAttempt={refreshStatus.last_attempt}
        />
      )}

      {data.status === "success" && !data.summary && data.departments.length === 0 ? (
        <EmptyState
          title="No dashboard data"
          description="Data will appear after the first sync completes. Try refreshing."
        />
      ) : (
        <>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <TotalPayrollCard
              value={data.status === "success" ? data.summary.total_payroll : 0}
              loading={loading}
            />
            <TotalClaimsCard
              value={data.status === "success" ? data.summary.total_claims : 0}
              loading={loading}
            />
            <TopDepartmentsCard
              departments={data.status === "success" ? data.departments : []}
              loading={loading}
            />
            <AnomalyHighlightsCard
              anomalies={data.status === "success" ? data.anomalies : []}
              loading={loading}
            />
          </div>

          <MonthlyTrendChart
            data={data.status === "success" ? mapToTrendChart(data.trends) : []}
            loading={loading}
          />

          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <DepartmentRankingChart
              data={data.status === "success" ? data.departments : []}
              loading={loading}
            />
            <ClaimTypeBreakdownChart
              data={data.status === "success" ? data.claimTypes : []}
              loading={loading}
            />
          </div>
        </>
      )}
    </div>
  );
}
