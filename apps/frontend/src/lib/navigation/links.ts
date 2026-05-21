import { ROUTES, type Severity, DETAIL_SOURCE } from "@/lib/constants";
import type { TimeRangeKey } from "./time-range";
import type { AnomalyPageState, DepartmentDetailState } from "./route-state";
import { writeAnomalyState, writeDepartmentDetailState } from "./route-state";

const appendQuery = (path: string, params: URLSearchParams): string => {
  const qs = params.toString();
  return qs ? `${path}?${qs}` : path;
}

export const buildDashboardToAnomaliesLink = (
  timeRange: TimeRangeKey,
): string => {
  const state: AnomalyPageState = { timeRange };
  return appendQuery(ROUTES.anomalies, writeAnomalyState(state));
}

export const buildDashboardToAnomaliesWithSeverityLink = (
  timeRange: TimeRangeKey,
  severity: Severity,
): string => {
  const state: AnomalyPageState = { timeRange, severity };
  return appendQuery(ROUTES.anomalies, writeAnomalyState(state));
}

export const buildDashboardToDepartmentDetailLink = (
  departmentId: string,
  timeRange: TimeRangeKey,
  source: typeof DETAIL_SOURCE.dashboardAttention | typeof DETAIL_SOURCE.dashboardRanking,
): string => {
  const state: DepartmentDetailState = { departmentId, timeRange, source };
  return appendQuery(
    ROUTES.departmentDetail(departmentId),
    writeDepartmentDetailState(state),
  );
}

export const buildDepartmentToAnomaliesLink = (
  departmentId: string,
  timeRange: TimeRangeKey,
): string => {
  const state: AnomalyPageState = { timeRange, departmentId };
  return appendQuery(ROUTES.anomalies, writeAnomalyState(state));
}

export const buildAnomalyToDepartmentDetailLink = (
  departmentId: string,
  timeRange: TimeRangeKey,
  anomalyId?: string,
): string => {
  const state: DepartmentDetailState = {
    departmentId,
    timeRange,
    source: DETAIL_SOURCE.anomalies,
    anomalyId,
  };
  return appendQuery(
    ROUTES.departmentDetail(departmentId),
    writeDepartmentDetailState(state),
  );
}
