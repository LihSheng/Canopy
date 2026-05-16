import type { TimeRangeKey } from "./time-range";
import type { AnomalyPageState, DepartmentDetailState } from "./route-state";
import { writeAnomalyState, writeDepartmentDetailState } from "./route-state";

export function buildDashboardToAnomaliesLink(
  timeRange: TimeRangeKey,
): string {
  const state: AnomalyPageState = { timeRange };
  return `/dashboard/anomalies?${writeAnomalyState(state).toString()}`;
}

export function buildDashboardToAnomaliesWithSeverityLink(
  timeRange: TimeRangeKey,
  severity: "high" | "medium" | "low",
): string {
  const state: AnomalyPageState = { timeRange, severity };
  return `/dashboard/anomalies?${writeAnomalyState(state).toString()}`;
}

export function buildDashboardToDepartmentDetailLink(
  departmentId: string,
  timeRange: TimeRangeKey,
  source: "dashboard_attention" | "dashboard_ranking",
): string {
  const state: DepartmentDetailState = { departmentId, timeRange, source };
  return `/dashboard/departments/${encodeURIComponent(departmentId)}?${writeDepartmentDetailState(state).toString()}`;
}
