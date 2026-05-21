import type { TimeRangeKey } from "@/lib/navigation/time-range";
import type { ExportJob } from "@/lib/api/types";

export type ExportPreset = {
  key: "executive_summary" | "department_spend" | "anomaly_review";
  label: string;
  description: string;
};

export const EXPORT_PRESETS: ExportPreset[] = [
  {
    key: "executive_summary",
    label: "Executive Summary",
    description: "Full overview with key metrics and trends",
  },
  {
    key: "department_spend",
    label: "Department Spend",
    description: "Spend breakdown across all departments",
  },
  {
    key: "anomaly_review",
    label: "Anomaly Review",
    description: "All detected anomalies with severity details",
  },
];

export type ExportHistoryItem = {
  id: string;
  presetName: string;
  status: "queued" | "running" | "completed" | "failed";
  createdAt: Date | null;
  timeRange: TimeRangeKey;
  snapshotTimestamp: string | null;
  errorSummary: string | null;
  downloadUrl: string | null;
};

export type ReportsWorkspaceView = {
  presets: ExportPreset[];
  recentExports: ExportHistoryItem[];
};

const mapStatus = (raw: string): ExportHistoryItem["status"] => {
  if (raw === "running" || raw === "completed" || raw === "failed") return raw;
  return "queued";
}

export const mapExportJob = (job: ExportJob): ExportHistoryItem => {
  return {
    id: job.id,
    presetName: job.preset_name,
    status: mapStatus(job.status),
    createdAt: job.started_at ? new Date(job.started_at) : null,
    timeRange: (job.time_range as TimeRangeKey) || "this_month",
    snapshotTimestamp: job.snapshot_timestamp,
    errorSummary: job.error_message,
    downloadUrl: job.status === "completed" ? `/api/exports/jobs/${job.id}/download` : null,
  };
}

export const mapReportsWorkspace = (jobs: ExportJob[]): ReportsWorkspaceView => {
  return {
    presets: EXPORT_PRESETS,
    recentExports: jobs.map(mapExportJob),
  };
}
