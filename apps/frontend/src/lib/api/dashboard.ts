import { request } from "./client";
import type {
  DashboardSummary,
  DepartmentSummary,
  MonthlyTrend,
  ClaimTypeBreakdown,
  Anomaly,
  DepartmentDetail,
  EmployeeContribution,
  ClaimDetail,
  RefreshStatus,
  MonthFilterParams,
} from "./types";

export function fetchSummary(): Promise<DashboardSummary> {
  return request<DashboardSummary>("/api/summary");
}

export function fetchDepartments(params?: MonthFilterParams): Promise<DepartmentSummary[]> {
  const qs = params ? `?year=${params.year}&month=${params.month}` : "";
  return request<DepartmentSummary[]>(`/api/departments${qs}`);
}

export function fetchMonthlyTrends(params?: MonthFilterParams): Promise<MonthlyTrend[]> {
  const qs = params ? `?year=${params.year}&month=${params.month}` : "";
  return request<MonthlyTrend[]>(`/api/trends${qs}`);
}

export function fetchClaimTypeBreakdown(params?: MonthFilterParams): Promise<ClaimTypeBreakdown[]> {
  const qs = params ? `?year=${params.year}&month=${params.month}` : "";
  return request<ClaimTypeBreakdown[]>(`/api/claims/breakdown${qs}`);
}

export function fetchAnomalies(): Promise<Anomaly[]> {
  return request<Anomaly[]>("/api/anomalies");
}

export function fetchDepartmentDetail(id: string, params?: MonthFilterParams): Promise<DepartmentDetail> {
  const qs = params ? `?year=${params.year}&month=${params.month}` : "";
  return request<DepartmentDetail>(`/api/departments/${id}${qs}`);
}

export function fetchEmployeeContributions(
  departmentId: string,
  params?: MonthFilterParams,
): Promise<EmployeeContribution[]> {
  const qs = params ? `?year=${params.year}&month=${params.month}` : "";
  return request<EmployeeContribution[]>(`/api/departments/${departmentId}/employees${qs}`);
}

export function fetchClaimDetails(
  departmentId?: string,
  params?: MonthFilterParams,
): Promise<ClaimDetail[]> {
  const parts: string[] = [];
  if (departmentId) parts.push(`department_id=${departmentId}`);
  if (params) parts.push(`year=${params.year}`, `month=${params.month}`);
  const qs = parts.length ? `?${parts.join("&")}` : "";
  return request<ClaimDetail[]>(`/api/claims${qs}`);
}

export function fetchRefreshStatus(): Promise<RefreshStatus> {
  return request<RefreshStatus>("/api/refresh/status");
}

export function triggerRefresh(): Promise<{ accepted: boolean }> {
  return request<{ accepted: boolean }>("/api/refresh", { method: "POST" });
}
