import type { TimeRangeKey } from "./time-range";
import type { AnomalyPageState, DepartmentDetailState } from "./route-state";
import { writeAnomalyState, writeDepartmentDetailState } from "./route-state";

function appendQuery(path: string, params: URLSearchParams): string {
  const qs = params.toString();
  return qs ? `${path}?${qs}` : path;
}

export function buildDashboardToAnomaliesLink(
  timeRange: TimeRangeKey,
): string {
  const state: AnomalyPageState = { timeRange };
  return appendQuery("/dashboard/anomalies", writeAnomalyState(state));
}

export function buildDashboardToAnomaliesWithSeverityLink(
  timeRange: TimeRangeKey,
  severity: "high" | "medium" | "low",
): string {
  const state: AnomalyPageState = { timeRange, severity };
  return appendQuery("/dashboard/anomalies", writeAnomalyState(state));
}

export function buildDashboardToDepartmentDetailLink(
  departmentId: string,
  timeRange: TimeRangeKey,
  source: "dashboard_attention" | "dashboard_ranking",
): string {
  const state: DepartmentDetailState = { departmentId, timeRange, source };
  return appendQuery(
    `/dashboard/departments/${encodeURIComponent(departmentId)}`,
    writeDepartmentDetailState(state),
  );
}
