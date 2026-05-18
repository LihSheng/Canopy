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

export interface ExportJob {
  id: string;
  status: string;
  preset_name: string;
  snapshot_id: string | null;
  time_range: string;
  snapshot_timestamp: string | null;
  started_at: string | null;
  finished_at: string | null;
  file_size_bytes: number | null;
  error_message: string | null;
}

export interface ExportHistory {
  jobs: ExportJob[];
}

export interface ExportTriggerResponse {
  accepted: boolean;
  job_id: string;
}

export interface Project {
  id: string;
  name: string;
  description: string;
  created_at: string;
  updated_at: string;
}

export interface SourceType {
  id: string;
  key: string;
  label: string;
  category: string;
  enabled: boolean;
  tags: string[];
  description: string;
}

export interface SheetProfile {
  sheet_name: string;
  row_count: number;
  data_row_count: number;
  column_count: number;
  header_row_index: number | null;
  confidence: number;
  warnings: string[];
  preview_columns: string[];
  preview_rows: (string | number | boolean | null)[][];
}

export interface StaticFilePreview {
  source_file_path: string;
  file_name: string;
  sheet_profiles: SheetProfile[];
}

export interface Connection {
  id: string;
  project_id: string;
  source_type: string;
  name: string;
  status: string;
  config_json: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface ConnectionDependencySummary {
  connection_id: string;
  active_dataset_count: number;
  active_run_count: number;
  can_delete: boolean;
}

export interface Dataset {
  id: string;
  project_id: string;
  connection_id: string;
  name: string;
  source_object_name: string;
  status: string;
  active_version_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface DatasetVersion {
  id: string;
  dataset_id: string;
  run_id: string;
  version_number: number;
  status: string;
  row_count: number;
  column_count: number;
  storage_path: string;
  cleaning_issues: { issue: string; column?: string; row?: number }[];
  created_at: string;
}

export interface Run {
  id: string;
  project_id: string;
  connection_id: string;
  dataset_id: string;
  status: string;
  started_by: string;
  started_at: string | null;
  finished_at: string | null;
  duration_ms: number | null;
  warning_count: number;
  error_message: string | null;
  created_at: string;
}

export interface TenantInfo {
  tenant_id: string;
  name: string;
  role: string;
}

export interface TenantContextResponse {
  tenant_id: string;
  role: string;
}

export interface DatasetHealth {
  dataset_id: string;
  row_count: number;
  column_count: number;
  missing_required_mappings: boolean;
  warning_count: number;
  last_run_status: string | null;
  last_published_version: number | null;
  freshness_at: string | null;
}
