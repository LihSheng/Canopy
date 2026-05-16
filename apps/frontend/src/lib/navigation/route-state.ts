import type { ReadonlyURLSearchParams } from "next/navigation";
import type { TimeRangeKey } from "./time-range";
import { parseTimeRange, DEFAULT_TIME_RANGE } from "./time-range";

export type DashboardPageState = {
  timeRange: TimeRangeKey;
};

export type AnomalyPageState = {
  timeRange: TimeRangeKey;
  departmentId?: string;
  severity?: "high" | "medium" | "low";
};

export type DepartmentDetailState = {
  departmentId: string;
  timeRange: TimeRangeKey;
  source?: "dashboard_attention" | "dashboard_ranking" | "anomalies";
  anomalyId?: string;
};

export function readDashboardState(params: URLSearchParams | ReadonlyURLSearchParams): DashboardPageState {
  return {
    timeRange: parseTimeRange(params.get("range")),
  };
}

export function readAnomalyState(params: URLSearchParams | ReadonlyURLSearchParams): AnomalyPageState {
  const severity = params.get("severity");
  return {
    timeRange: parseTimeRange(params.get("range")),
    departmentId: params.get("department_id") ?? undefined,
    severity:
      severity === "high" || severity === "medium" || severity === "low"
        ? severity
        : undefined,
  };
}

export function readDepartmentDetailState(
  params: URLSearchParams | ReadonlyURLSearchParams,
): DepartmentDetailState {
  const source = params.get("source");
  return {
    departmentId: params.get("department_id") ?? "",
    timeRange: parseTimeRange(params.get("range")),
    source:
      source === "dashboard_attention" ||
      source === "dashboard_ranking" ||
      source === "anomalies"
        ? source
        : undefined,
    anomalyId: params.get("anomaly_id") ?? undefined,
  };
}

export function writeDashboardState(state: DashboardPageState): URLSearchParams {
  const params = new URLSearchParams();
  if (state.timeRange !== DEFAULT_TIME_RANGE) {
    params.set("range", state.timeRange);
  }
  return params;
}

export function writeAnomalyState(state: AnomalyPageState): URLSearchParams {
  const params = new URLSearchParams();
  if (state.timeRange !== DEFAULT_TIME_RANGE) {
    params.set("range", state.timeRange);
  }
  if (state.departmentId) {
    params.set("department_id", state.departmentId);
  }
  if (state.severity) {
    params.set("severity", state.severity);
  }
  return params;
}

export function writeDepartmentDetailState(state: DepartmentDetailState): URLSearchParams {
  const params = new URLSearchParams();
  if (state.timeRange !== DEFAULT_TIME_RANGE) {
    params.set("range", state.timeRange);
  }
  if (state.departmentId) {
    params.set("department_id", state.departmentId);
  }
  if (state.source) {
    params.set("source", state.source);
  }
  if (state.anomalyId) {
    params.set("anomaly_id", state.anomalyId);
  }
  return params;
}
