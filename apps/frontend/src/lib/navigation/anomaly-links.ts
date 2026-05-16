import type { TimeRangeKey } from "./time-range";
import type { DepartmentDetailState } from "./route-state";
import { writeDepartmentDetailState } from "./route-state";

export function buildAnomalyToDepartmentDetailLink(
  departmentId: string,
  timeRange: TimeRangeKey,
  anomalyId?: string,
): string {
  const state: DepartmentDetailState = {
    departmentId,
    timeRange,
    source: "anomalies",
    anomalyId,
  };
  return `/dashboard/departments/${encodeURIComponent(departmentId)}?${writeDepartmentDetailState(state).toString()}`;
}
