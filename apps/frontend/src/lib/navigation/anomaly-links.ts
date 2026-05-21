import type { TimeRangeKey } from "./time-range";
import type { DepartmentDetailState } from "./route-state";
import { writeDepartmentDetailState } from "./route-state";
import { ROUTES, DETAIL_SOURCE } from "@/lib/constants";

export function buildAnomalyToDepartmentDetailLink(
  departmentId: string,
  timeRange: TimeRangeKey,
  anomalyId?: string,
): string {
  const state: DepartmentDetailState = {
    departmentId,
    timeRange,
    source: DETAIL_SOURCE.anomalies,
    anomalyId,
  };
  return `${ROUTES.departmentDetail(departmentId)}?${writeDepartmentDetailState(state).toString()}`;
}
