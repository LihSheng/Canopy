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
  category?: string;
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
  test_status?: string | null;
  last_tested_at?: string | null;
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
  sync_mode?: string | null;
  batch_strategy?: string | null;
  real_time_strategy?: string | null;
  cursor_column?: string | null;
  last_cursor_value?: string | null;
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
  failure_reason?: string;
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

export interface DriftStatus {
  drift_detected: boolean;
  is_blocked: boolean;
  last_drift_at: string | null;
  last_drift_is_breaking: boolean | null;
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
  schema_drift: DriftStatus | null;
}

export interface DriftEvent {
  id: string;
  connection_id: string;
  source_object_name: string;
  dataset_id: string | null;
  drift_type: string;
  before_hash: string;
  after_hash: string;
  delta: {
    added: unknown[];
    removed: unknown[];
    renamed: { old: unknown; new: unknown }[];
    type_changed: { old: unknown; new: unknown }[];
    is_breaking: boolean;
    severity: string;
  };
  is_breaking: boolean;
  detected_by: string;
  created_at: string;
}

export interface DatasetDeleteSummary {
  dataset_id: string;
  version_count: number;
  active_run_count: number;
  can_delete: boolean;
  blocking_reason: string | null;
}

export interface DatasetBulkDeleteSummaryItem {
  dataset_id: string;
  version_count: number;
  active_run_count: number;
  can_delete: boolean;
  blocking_reason: string | null;
  dataset_name: string | null;
}

export interface DatasetBulkDeleteSkippedItem {
  dataset_id: string;
  dataset_name: string | null;
  reason: string;
}

export interface DatasetBulkDeleteDeletedItem {
  dataset_id: string;
  dataset_name: string;
}

export interface DatasetBulkDeleteResult {
  deleted: DatasetBulkDeleteDeletedItem[];
  skipped: DatasetBulkDeleteSkippedItem[];
  total_requested: number;
}

export interface DatasetVersionDeleteSummary {
  dataset_id: string;
  version_id: string;
  version_number: number;
  is_active_version: boolean;
  can_delete: boolean;
  blocking_reason: string | null;
}

export interface ConnectionTestResult {
  success: boolean;
  message?: string;
  supports_cdc?: boolean;
  cdc_parameters?: Record<string, unknown>;
}

export interface ColumnSchema {
  name: string;
  data_type: string;
}

export interface DiscoveredTable {
  table_name: string;
  row_count_estimate: number;
  columns: ColumnSchema[];
  detected_cursor_column: string | null;
}

export interface TablePreview {
  columns: ColumnSchema[];
  rows: (string | number | boolean | null)[][];
  detected_cursor_column: string | null;
  cursor_candidates: string[];
}

export interface SyncPolicyUpdate {
  sync_mode?: string | null;
  batch_strategy?: string | null;
  real_time_strategy?: string | null;
  cursor_column?: string | null;
  frequency_minutes?: number | null;
}

// ─── Retention Policy ───

export type RetentionPreset =
  | "retain_indefinitely"
  | "30_days"
  | "90_days"
  | "1_year"
  | "7_years"
  | "custom";

export type RetentionMode =
  | "retain_indefinitely"
  | "expire_after"
  | "review_after";

export interface RetentionPolicy {
  dataset_id: string;
  id: string | null;
  mode: RetentionMode;
  horizon_days: number | null;
  preset: RetentionPreset;
  is_active: boolean;
  calculated_next_action_at: string | null;
  created_by: string | null;
  updated_by: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface RetentionPolicyUpdate {
  preset: RetentionPreset;
  mode?: RetentionMode | null;
  horizon_days?: number | null;
}

// ─── Semantic Mapping (Entity Tab) ───

export interface ObjectType {
  id: string;
  tenant_id: string;
  object_type_key: string;
  display_name: string;
  description: string;
  created_at: string;
  updated_at: string | null;
}

export interface SchemaColumn {
  column_name: string;
  primitive_type: string;
}

export interface PropertyMapping {
  source_column: string;
  property_name: string;
  semantic_type: string;
  included: boolean;
  is_primary_key: boolean;
}

export interface EntityLink {
  link_id: string;
  display_name: string;
  source_property_key: string;
  target_object_type_id: string;
  target_property_key: string;
  cardinality: string;
}

export interface SourceNode {
  source_id: string;
  source_type: string;
  name: string;
  reference_id: string;
  fields: string[];
}

export interface FieldRef {
  source_id: string;
  source_name: string;
  field_name: string;
}

export interface ComputedProperty {
  id: string;
  property_name: string;
  semantic_type: string;
  composition_kind: string;
  expression: string;
  inputs: FieldRef[];
  included: boolean;
}

export interface SemanticMapping {
  id: string;
  dataset_id: string;
  dataset_version_id: string;
  version_number: number;
  object_type_id: string;
  object_type_key: string;
  properties: PropertyMapping[];
  links: EntityLink[];
  source_nodes: SourceNode[];
  computed_properties: ComputedProperty[];
  layout_state: Record<string, unknown>;
  created_at: string;
  updated_at: string | null;
}

export interface ValidationErrorItem {
  field: string;
  value: string | null;
  message: string;
}

export interface ValidationResult {
  valid: boolean;
  errors: ValidationErrorItem[];
}

// ─── Entity Registry (central entity area) ───

export interface EntityRegistryItem {
  id: string;
  object_type_key: string;
  display_name: string;
  description: string;
  created_at: string;
  updated_at: string | null;
  dataset_name: string | null;
  dataset_id: string | null;
  mapping_version: number | null;
  property_count: number;
  link_count: number;
  computed_property_count: number;
  mapping_updated_at: string | null;
}

export interface EntityDetail {
  id: string;
  object_type_key: string;
  display_name: string;
  description: string;
  created_at: string;
  updated_at: string | null;
  dataset_name: string | null;
  mapping: EntityMappingDetail | null;
}

export interface EntityMappingDetail {
  id: string;
  dataset_id: string;
  dataset_version_id: string;
  version_number: number;
  properties: PropertyMapping[];
  links: EntityLink[];
  source_nodes: SourceNode[];
  computed_properties: ComputedProperty[];
  layout_state: Record<string, unknown>;
  created_at: string;
  updated_at: string | null;
}
