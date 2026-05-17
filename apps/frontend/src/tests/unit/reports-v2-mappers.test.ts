import { describe, expect, it } from "vitest";
import {
  mapExportJob,
  mapReportsWorkspace,
  EXPORT_PRESETS,
} from "@/components/reports/report-mappers";
import type { ExportJob } from "@/lib/api/types";

const mockCompletedJob: ExportJob = {
  id: "exp-001",
  status: "completed",
  preset_name: "Executive Summary",
  snapshot_id: "snap-123",
  time_range: "this_month",
  snapshot_timestamp: "2026-05-16T10:30:00Z",
  started_at: "2026-05-16T10:00:00Z",
  finished_at: "2026-05-16T10:30:00Z",
  file_size_bytes: 12500,
  error_message: null,
};

const mockFailedJob: ExportJob = {
  id: "exp-002",
  status: "failed",
  preset_name: "Department Spend",
  snapshot_id: null,
  time_range: "last_3_months",
  snapshot_timestamp: null,
  started_at: "2026-05-16T09:00:00Z",
  finished_at: "2026-05-16T09:01:00Z",
  file_size_bytes: null,
  error_message: "Database connection refused",
};

const mockPendingJob: ExportJob = {
  id: "exp-003",
  status: "pending",
  preset_name: "Anomaly Review",
  snapshot_id: null,
  time_range: "last_12_months",
  snapshot_timestamp: null,
  started_at: null,
  finished_at: null,
  file_size_bytes: null,
  error_message: null,
};

const mockRunningJob: ExportJob = {
  id: "exp-004",
  status: "running",
  preset_name: "Executive Summary",
  snapshot_id: null,
  time_range: "this_month",
  snapshot_timestamp: null,
  started_at: "2026-05-16T11:00:00Z",
  finished_at: null,
  file_size_bytes: null,
  error_message: null,
};

describe("mapExportJob", () => {
  it("maps completed job correctly", () => {
    const result = mapExportJob(mockCompletedJob);
    expect(result.id).toBe("exp-001");
    expect(result.status).toBe("completed");
    expect(result.presetName).toBe("Executive Summary");
    expect(result.timeRange).toBe("this_month");
    expect(result.snapshotTimestamp).toBe("2026-05-16T10:30:00Z");
    expect(result.errorSummary).toBeNull();
    expect(result.downloadUrl).toBe("/api/exports/jobs/exp-001/download");
    expect(result.createdAt).toBeInstanceOf(Date);
  });

  it("maps failed job with error summary", () => {
    const result = mapExportJob(mockFailedJob);
    expect(result.status).toBe("failed");
    expect(result.errorSummary).toBe("Database connection refused");
    expect(result.downloadUrl).toBeNull();
  });

  it("maps pending job as queued status", () => {
    const result = mapExportJob(mockPendingJob);
    expect(result.status).toBe("queued");
    expect(result.createdAt).toBeNull();
    expect(result.downloadUrl).toBeNull();
  });

  it("maps running job correctly", () => {
    const result = mapExportJob(mockRunningJob);
    expect(result.status).toBe("running");
    expect(result.downloadUrl).toBeNull();
    expect(result.createdAt).toBeInstanceOf(Date);
  });

  it("maps time_range correctly across all presets", () => {
    const thisMonth = mapExportJob(mockCompletedJob);
    const threeMonths = mapExportJob(mockFailedJob);
    const twelveMonths = mapExportJob(mockPendingJob);

    expect(thisMonth.timeRange).toBe("this_month");
    expect(threeMonths.timeRange).toBe("last_3_months");
    expect(twelveMonths.timeRange).toBe("last_12_months");
  });
});

describe("mapReportsWorkspace", () => {
  it("includes all three presets", () => {
    const result = mapReportsWorkspace([]);
    expect(result.presets).toHaveLength(3);
    expect(result.presets[0].label).toBe("Executive Summary");
    expect(result.presets[1].label).toBe("Department Spend");
    expect(result.presets[2].label).toBe("Anomaly Review");
  });

  it("maps multiple jobs to history items", () => {
    const result = mapReportsWorkspace([mockCompletedJob, mockFailedJob]);
    expect(result.recentExports).toHaveLength(2);
    expect(result.recentExports[0].status).toBe("completed");
    expect(result.recentExports[1].status).toBe("failed");
  });

  it("returns empty recent exports when no jobs", () => {
    const result = mapReportsWorkspace([]);
    expect(result.recentExports).toHaveLength(0);
  });

  it("preserves preset keys on presets", () => {
    const result = mapReportsWorkspace([]);
    expect(result.presets[0].key).toBe("executive_summary");
    expect(result.presets[1].key).toBe("department_spend");
    expect(result.presets[2].key).toBe("anomaly_review");
  });
});

describe("EXPORT_PRESETS", () => {
  it("has three presets with unique keys", () => {
    const keys = EXPORT_PRESETS.map((p) => p.key);
    expect(keys).toHaveLength(3);
    expect(new Set(keys).size).toBe(3);
  });

  it("all presets have labels and descriptions", () => {
    for (const preset of EXPORT_PRESETS) {
      expect(preset.label).toBeTruthy();
      expect(preset.description).toBeTruthy();
    }
  });
});
