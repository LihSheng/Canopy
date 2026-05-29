import { request } from "./client";

export interface HealthSummary {
  bytes_written_30d: number;
  error_count_30d: number;
  warning_count_30d: number;
  sla_violation_count_30d: number;
  total_runs_30d: number;
  active_pipeline_count: number;
  recent_failures: FailureRun[];
}

export interface FailureRun {
  id: string;
  run_id: string;
  pipeline_id: string;
  job_type: string;
  dataset_id: string | null;
  connection_id: string | null;
  status: string;
  duration_ms: number;
  bytes_written: number;
  rows_processed: number;
  error_message: string;
  warning_message: string;
  latency_threshold_ms: number | null;
  started_at: string | null;
  finished_at: string | null;
  created_at: string;
}

export interface DailyTrend {
  date: string;
  bytes_written: number;
  errors: number;
  sla_violations: number;
  run_count: number;
}

export interface PipelineSummary {
  pipeline_id: string;
  job_type: string;
  health: "healthy" | "degraded" | "failed";
  total_runs: number;
  total_failures: number;
  total_bytes_written: number;
  total_sla_violations: number;
  max_duration_ms: number;
}

export interface PipelineDetail extends PipelineSummary {
  days_active: number;
  total_successes: number;
  total_warnings: number;
  total_rows_processed: number;
  avg_duration_ms: number;
  recent_runs: FailureRun[];
}

export interface RunDetail {
  run_id: string;
  steps: FailureRun[];
}

export const getHealthSummary = async (): Promise<HealthSummary> => {
  return request<HealthSummary>("/api/admin/health/summary");
};

export const getHealthTrends = async (days: number = 30): Promise<DailyTrend[]> => {
  return request<DailyTrend[]>(`/api/admin/health/trends?days=${days}`);
};

export const getPipelineCatalog = async (
  healthFilter?: string
): Promise<PipelineSummary[]> => {
  const path = healthFilter
    ? `/api/admin/health/pipelines?health_filter=${healthFilter}`
    : "/api/admin/health/pipelines";
  return request<PipelineSummary[]>(path);
};

export const getPipelineDetail = async (
  pipelineId: string
): Promise<PipelineDetail> => {
  return request<PipelineDetail>(`/api/admin/health/pipelines/${pipelineId}`);
};

export const getRunDetail = async (runId: string): Promise<RunDetail> => {
  return request<RunDetail>(`/api/admin/health/runs/${runId}`);
};

export const refreshHealthRollups = async (): Promise<{ refreshed: boolean; date: string }> => {
  return request<{ refreshed: boolean; date: string }>("/api/admin/health/refresh", {
    method: "POST",
  });
};

export const backfillHealthRollups = async (
  days: number = 30
): Promise<{ backfilled: boolean; days: number }> => {
  return request<{ backfilled: boolean; days: number }>(`/api/admin/health/backfill?days=${days}`, {
    method: "POST",
  });
};
