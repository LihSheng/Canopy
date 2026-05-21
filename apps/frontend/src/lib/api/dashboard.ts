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

export const fetchSummary = (): Promise<DashboardSummary> => {
  return request<DashboardSummary>("/api/dashboard/summary");
}

export const fetchDepartments = (params?: MonthFilterParams): Promise<DepartmentSummary[]> => {
  const qs = params ? `?year=${params.year}&month=${params.month}` : "";
  return request<DepartmentSummary[]>(`/api/departments${qs}`);
}

export const fetchMonthlyTrends = (params?: MonthFilterParams): Promise<MonthlyTrend[]> => {
  const qs = params ? `?year=${params.year}&month=${params.month}` : "";
  return request<MonthlyTrend[]>(`/api/dashboard/trends${qs}`);
}

export const fetchClaimTypeBreakdown = (params?: MonthFilterParams): Promise<ClaimTypeBreakdown[]> => {
  const qs = params ? `?year=${params.year}&month=${params.month}` : "";
  return request<ClaimTypeBreakdown[]>(`/api/dashboard/claim-types${qs}`);
}

export const fetchAnomalies = (): Promise<Anomaly[]> => {
  return request<Anomaly[]>("/api/anomalies");
}

export const fetchDepartmentDetail = (id: string, params?: MonthFilterParams): Promise<DepartmentDetail> => {
  const qs = params ? `?year=${params.year}&month=${params.month}` : "";
  return request<DepartmentDetail>(`/api/departments/${id}${qs}`);
}

export const fetchEmployeeContributions = (
  departmentId: string,
  params?: MonthFilterParams,
): Promise<EmployeeContribution[]> => {
  const qs = params ? `?year=${params.year}&month=${params.month}` : "";
  return request<EmployeeContribution[]>(`/api/departments/${departmentId}/employees${qs}`);
}

export const fetchClaimDetails = (
  departmentId?: string,
  params?: MonthFilterParams,
): Promise<ClaimDetail[]> => {
  const parts: string[] = [];
  if (departmentId) parts.push(`department_id=${departmentId}`);
  if (params) parts.push(`year=${params.year}`, `month=${params.month}`);
  const qs = parts.length ? `?${parts.join("&")}` : "";
  return request<ClaimDetail[]>(`/api/claims${qs}`);
}

export const fetchRefreshStatus = (): Promise<RefreshStatus> => {
  return request<RefreshStatus>("/api/refresh/current");
}

export const triggerRefresh = (): Promise<{ accepted: boolean }> => {
  return request<{ accepted: boolean }>("/api/refresh", { method: "POST" });
}
