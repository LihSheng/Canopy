import { ROUTES, type Severity, DETAIL_SOURCE } from "@/lib/constants";
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
  return appendQuery(ROUTES.anomalies, writeAnomalyState(state));
}

export function buildDashboardToAnomaliesWithSeverityLink(
  timeRange: TimeRangeKey,
  severity: Severity,
): string {
  const state: AnomalyPageState = { timeRange, severity };
  return appendQuery(ROUTES.anomalies, writeAnomalyState(state));
}

export function buildDashboardToDepartmentDetailLink(
  departmentId: string,
  timeRange: TimeRangeKey,
  source: typeof DETAIL_SOURCE.dashboardAttention | typeof DETAIL_SOURCE.dashboardRanking,
): string {
  const state: DepartmentDetailState = { departmentId, timeRange, source };
  return appendQuery(
    ROUTES.departmentDetail(departmentId),
    writeDepartmentDetailState(state),
  );
}
