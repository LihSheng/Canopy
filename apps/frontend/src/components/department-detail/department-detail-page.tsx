"use client";

import { useCallback, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { AnalyticsPageShell } from "@/components/analytics-shell/analytics-page-shell";
import { ErrorState } from "@/components/shared/error-state";
import { EmptyState } from "@/components/shared/empty-state";
import { DepartmentDetailHeader } from "./department-detail-header";
import { DepartmentTrendPanel, DepartmentTrendPanelSkeleton } from "./department-trend-panel";
import { DepartmentAiSummary, DepartmentAiSummarySkeleton } from "./department-ai-summary";
import { DepartmentContributorsSplit, DepartmentContributorsSplitSkeleton } from "./department-contributors-split";
import { mapDepartmentDetailView } from "./department-detail-mappers";
import type { DepartmentDetailView } from "./department-detail-mappers";
import { readDepartmentDetailState } from "@/lib/navigation/route-state";
import { buildDepartmentToAnomaliesLink } from "@/lib/navigation/links";
import { TIME_RANGE_LABELS, type TimeRangeKey } from "@/lib/navigation/time-range";
import { request } from "@/lib/api/client";
import {
  fetchDepartmentDetail,
  fetchEmployeeContributions,
  fetchClaimDetails,
  fetchAnomalies,
} from "@/lib/api/dashboard";
import type { MonthlyTrend } from "@/lib/api/types";

type Props = {
  id: string;
};

type DataState =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "success"; view: DepartmentDetailView };

export const DepartmentDetailPage = ({ id }: Props) => {
  const searchParams = useSearchParams();
  const state = readDepartmentDetailState(searchParams);

  const [timeRange, setTimeRange] = useState<TimeRangeKey>(state.timeRange);
  const [data, setData] = useState<DataState>({ status: "loading" });

  const load = useCallback(async () => {
    setData({ status: "loading" });
    try {
      const [department, employees, claims, anomalies, trends] = await Promise.all([
        fetchDepartmentDetail(id),
        fetchEmployeeContributions(id),
        fetchClaimDetails(id),
        fetchAnomalies(),
        request<MonthlyTrend[]>(`/api/departments/${id}/trends`),
      ]);
      const view = mapDepartmentDetailView(department, employees, claims, trends, anomalies, timeRange);
      setData({ status: "success", view });
    } catch (err) {
      setData({
        status: "error",
        message: err instanceof Error ? err.message : "Failed to load department detail",
      });
    }
  }, [id, timeRange]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- initial data fetch
    load();
  }, [load]);

  const contextLabel = TIME_RANGE_LABELS[timeRange];

  const loading = data.status === "loading";
  const view = data.status === "success" ? data.view : null;

  const breadcrumbItems = [
    { label: "Dashboard", href: "/dashboard" },
    { label: "Departments", href: "/dashboard/departments" },
    { label: view ? view.department.name : "Loading..." },
  ];

  if (data.status === "error") {
    return (
      <AnalyticsPageShell title="Department Detail" contextText={contextLabel} breadcrumbItems={breadcrumbItems}>
        <ErrorState message={data.message} onRetry={load} />
      </AnalyticsPageShell>
    );
  }

  return (
    <AnalyticsPageShell
      header={
        <DepartmentDetailHeader
          summary={{
            departmentName: view ? view.department.name : "Loading...",
            attentionState: view?.department.attentionState ?? null,
            totalSpend: view ? view.summary.totalSpend : 0,
            changePercent: view ? view.summary.changePercent : 0,
          }}
          timeRange={timeRange}
          onTimeRangeChange={setTimeRange}
        />
      }
      breadcrumbItems={breadcrumbItems}
    >
      {loading && (
        <div className="space-y-6">
          <DepartmentTrendPanelSkeleton />
          <DepartmentAiSummarySkeleton />
          <DepartmentContributorsSplitSkeleton />
        </div>
      )}

      {view && view.topEmployees.length === 0 && view.topClaimTypes.length === 0 && (
        <EmptyState
          variant="minimal"
          title="No department data"
          description="Data will appear after the first sync completes."
        />
      )}

      {view && (view.topEmployees.length > 0 || view.topClaimTypes.length > 0) && (
        <div className="space-y-6">
          <DepartmentTrendPanel series={view.trend} />

          <DepartmentAiSummary summary={view.aiSummary} />

          <DepartmentContributorsSplit
            topEmployees={view.topEmployees}
            topClaimTypes={view.topClaimTypes}
          />

          <div className="flex justify-end">
            <Link
              href={buildDepartmentToAnomaliesLink(view.department.id, timeRange)}
              className="inline-flex items-center gap-1.5 rounded-lg border border-zinc-200 bg-white px-4 py-2 text-sm font-medium text-zinc-600 transition-colors hover:border-zinc-300 hover:text-zinc-900"
            >
              View related anomalies
              <svg
                viewBox="0 0 20 20"
                fill="currentColor"
                className="h-4 w-4"
              >
                <path
                  fillRule="evenodd"
                  d="M8.22 5.22a.75.75 0 01 1.06 0l4.25 4.25a.75.75 0 010 1.06l-4.25 4.25a.75.75 0 01-1.06-1.06L11.94 10 8.22 6.28a.75.75 0 010-1.06z"
                  clipRule="evenodd"
                />
              </svg>
            </Link>
          </div>
        </div>
      )}
    </AnalyticsPageShell>
  );
}
