import type { ReadonlyURLSearchParams } from "next/navigation";
import { QUERY_PARAMS, SEVERITIES, DETAIL_SOURCE } from "@/lib/constants";
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
    timeRange: parseTimeRange(params.get(QUERY_PARAMS.range)),
  };
}

export function readAnomalyState(params: URLSearchParams | ReadonlyURLSearchParams): AnomalyPageState {
  const severity = params.get(QUERY_PARAMS.severity);
  return {
    timeRange: parseTimeRange(params.get(QUERY_PARAMS.range)),
    departmentId: params.get(QUERY_PARAMS.departmentId) ?? undefined,
    severity:
      SEVERITIES.includes(severity as "high" | "medium" | "low")
        ? (severity as "high" | "medium" | "low")
        : undefined,
  };
}

export function readDepartmentDetailState(
  params: URLSearchParams | ReadonlyURLSearchParams,
): DepartmentDetailState {
  const source = params.get(QUERY_PARAMS.source);
  return {
    departmentId: params.get(QUERY_PARAMS.departmentId) ?? "",
    timeRange: parseTimeRange(params.get(QUERY_PARAMS.range)),
    source:
      source === DETAIL_SOURCE.dashboardAttention ||
      source === DETAIL_SOURCE.dashboardRanking ||
      source === DETAIL_SOURCE.anomalies
        ? source
        : undefined,
    anomalyId: params.get(QUERY_PARAMS.anomalyId) ?? undefined,
  };
}

export function writeDashboardState(state: DashboardPageState): URLSearchParams {
  const params = new URLSearchParams();
  if (state.timeRange !== DEFAULT_TIME_RANGE) {
    params.set(QUERY_PARAMS.range, state.timeRange);
  }
  return params;
}

export function writeAnomalyState(state: AnomalyPageState): URLSearchParams {
  const params = new URLSearchParams();
  if (state.timeRange !== DEFAULT_TIME_RANGE) {
    params.set(QUERY_PARAMS.range, state.timeRange);
  }
  if (state.departmentId) {
    params.set(QUERY_PARAMS.departmentId, state.departmentId);
  }
  if (state.severity) {
    params.set(QUERY_PARAMS.severity, state.severity);
  }
  return params;
}

export function writeDepartmentDetailState(state: DepartmentDetailState): URLSearchParams {
  const params = new URLSearchParams();
  if (state.timeRange !== DEFAULT_TIME_RANGE) {
    params.set(QUERY_PARAMS.range, state.timeRange);
  }
  if (state.departmentId) {
    params.set(QUERY_PARAMS.departmentId, state.departmentId);
  }
  if (state.source) {
    params.set(QUERY_PARAMS.source, state.source);
  }
  if (state.anomalyId) {
    params.set(QUERY_PARAMS.anomalyId, state.anomalyId);
  }
  return params;
}
