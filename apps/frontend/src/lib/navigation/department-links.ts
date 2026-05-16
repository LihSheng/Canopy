import type { TimeRangeKey } from "./time-range";
import type { AnomalyPageState } from "./route-state";
import { writeAnomalyState } from "./route-state";

export function buildDepartmentToAnomaliesLink(
  departmentId: string,
  timeRange: TimeRangeKey,
): string {
  const state: AnomalyPageState = { timeRange, departmentId };
  return `/dashboard/anomalies?${writeAnomalyState(state).toString()}`;
}
