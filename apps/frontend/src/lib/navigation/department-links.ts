import type { TimeRangeKey } from "./time-range";
import type { AnomalyPageState } from "./route-state";
import { writeAnomalyState } from "./route-state";
import { ROUTES } from "@/lib/constants";

export function buildDepartmentToAnomaliesLink(
  departmentId: string,
  timeRange: TimeRangeKey,
): string {
  const state: AnomalyPageState = { timeRange, departmentId };
  return `${ROUTES.anomalies}?${writeAnomalyState(state).toString()}`;
}
