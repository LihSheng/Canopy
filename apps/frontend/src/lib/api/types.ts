export interface DashboardSummary {
  total_payroll: number;
  total_claims: number;
  period: { year: number; month: number };
  department_count: number;
  anomaly_count: number;
  last_updated: string;
}

export interface DepartmentSummary {
  id: string;
  name: string;
  total_spend: number;
  payroll_spend: number;
  claims_spend: number;
  change_pct: number;
}

export interface MonthlyTrend {
  month: string;
  payroll: number;
  claims: number;
  total: number;
}

export interface ClaimTypeBreakdown {
  type: string;
  amount: number;
  count: number;
}

export interface Anomaly {
  id: string;
  department_id: string;
  department_name: string;
  period: string;
  description: string;
  severity: "low" | "medium" | "high";
  change_pct: number;
}

export interface DepartmentDetail {
  id: string;
  name: string;
  payroll_spend: number;
  claims_spend: number;
  total_spend: number;
  change_pct: number;
  employee_count: number;
}

export interface EmployeeContribution {
  id: string;
  name: string;
  department: string;
  payroll: number;
  claims: number;
  total: number;
}

export interface ClaimDetail {
  id: string;
  employee_name: string;
  department: string;
  type: string;
  amount: number;
  date: string;
}

export interface RefreshStatus {
  status: "idle" | "queued" | "running" | "completed" | "failed";
  last_refresh: string | null;
  last_attempt: string | null;
  error_message: string | null;
}

export interface MonthFilterParams {
  year: number;
  month: number;
}
