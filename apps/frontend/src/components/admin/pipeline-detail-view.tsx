"use client";

import type { PipelineDetail } from "@/lib/api/admin-health";

interface PipelineDetailViewProps {
  detail: PipelineDetail | null;
  loading: boolean;
  onRunClick: (runId: string) => void;
}

export const PipelineDetailView = ({
  detail,
  loading,
  onRunClick,
}: PipelineDetailViewProps) => {
  if (loading) {
    return (
      <div className="flex min-h-48 items-center justify-center">
        <p className="text-sm text-zinc-500">Loading pipeline detail...</p>
      </div>
    );
  }

  if (!detail) {
    return (
      <div className="flex min-h-48 items-center justify-center">
        <p className="text-sm text-zinc-500">Pipeline not found</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-xl font-bold text-zinc-900">{detail.pipeline_id}</h2>
        <p className="text-sm text-zinc-500">Job type: {detail.job_type}</p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
        <SummaryCard label="Total Runs" value={detail.total_runs.toString()} />
        <SummaryCard
          label="Success Rate"
          value={
            detail.total_runs > 0
              ? `${((detail.total_successes / detail.total_runs) * 100).toFixed(1)}%`
              : "-"
          }
        />
        <SummaryCard label="Failures" value={detail.total_failures.toString()} variant="danger" />
        <SummaryCard label="Warnings" value={detail.total_warnings.toString()} variant="warning" />
        <SummaryCard
          label="SLA Violations"
          value={detail.total_sla_violations.toString()}
          variant={detail.total_sla_violations > 0 ? "warning" : "normal"}
        />
        <SummaryCard
          label="Bytes Written"
          value={formatBytes(detail.total_bytes_written)}
        />
        <SummaryCard
          label="Rows Processed"
          value={detail.total_rows_processed.toLocaleString()}
        />
        <SummaryCard
          label="Avg Duration"
          value={formatDuration(detail.avg_duration_ms)}
        />
        <SummaryCard
          label="Max Duration"
          value={formatDuration(detail.max_duration_ms)}
        />
        <SummaryCard label="Days Active" value={detail.days_active.toString()} />
      </div>

      {/* Recent Runs */}
      <div className="rounded-lg border border-zinc-200 bg-white">
        <div className="border-b border-zinc-200 px-4 py-3">
          <h3 className="text-sm font-semibold text-zinc-900">Recent Runs</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-zinc-200">
            <thead className="bg-zinc-50">
              <tr>
                <th className="px-4 py-2 text-left text-xs font-medium uppercase tracking-wider text-zinc-500">
                  Run ID
                </th>
                <th className="px-4 py-2 text-left text-xs font-medium uppercase tracking-wider text-zinc-500">
                  Status
                </th>
                <th className="px-4 py-2 text-right text-xs font-medium uppercase tracking-wider text-zinc-500">
                  Duration
                </th>
                <th className="px-4 py-2 text-left text-xs font-medium uppercase tracking-wider text-zinc-500">
                  Error
                </th>
                <th className="px-4 py-2 text-left text-xs font-medium uppercase tracking-wider text-zinc-500">
                  Finished At
                </th>
                <th className="px-4 py-2 text-left text-xs font-medium uppercase tracking-wider text-zinc-500">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-200">
              {detail.recent_runs.length === 0 ? (
                <tr>
                  <td
                    colSpan={6}
                    className="px-4 py-8 text-center text-sm text-zinc-500"
                  >
                    No recent runs
                  </td>
                </tr>
              ) : (
                detail.recent_runs.map((r) => (
                  <tr key={r.id} className="hover:bg-zinc-50">
                    <td className="max-w-[120px] truncate px-4 py-2 text-sm font-mono text-zinc-900">
                      {r.run_id}
                    </td>
                    <td className="whitespace-nowrap px-4 py-2">
                      <span
                        className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${
                          r.status === "failed"
                            ? "bg-red-100 text-red-800"
                            : r.status === "warning"
                              ? "bg-amber-100 text-amber-800"
                              : "bg-green-100 text-green-800"
                        }`}
                      >
                        {r.status}
                      </span>
                    </td>
                    <td className="whitespace-nowrap px-4 py-2 text-right text-sm text-zinc-500">
                      {formatDuration(r.duration_ms)}
                    </td>
                    <td className="max-w-xs truncate px-4 py-2 text-sm text-red-700">
                      {r.error_message || "-"}
                    </td>
                    <td className="whitespace-nowrap px-4 py-2 text-sm text-zinc-500">
                      {r.finished_at
                        ? new Date(r.finished_at).toLocaleString()
                        : "-"}
                    </td>
                    <td className="whitespace-nowrap px-4 py-2 text-sm">
                      <button
                        onClick={() => onRunClick(r.run_id)}
                        className="font-medium text-indigo-600 hover:text-indigo-800"
                      >
                        View
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

const SummaryCard = ({
  label,
  value,
  variant = "normal",
}: {
  label: string;
  value: string;
  variant?: "normal" | "warning" | "danger";
}) => {
  const variantStyles = {
    normal: "",
    warning: "bg-amber-50 border-amber-200",
    danger: "bg-red-50 border-red-200",
  };
  return (
    <div
      className={`rounded-lg border border-zinc-200 px-4 py-3 ${variantStyles[variant]}`}
    >
      <p className="text-xs font-medium uppercase tracking-wider text-zinc-500">
        {label}
      </p>
      <p className="mt-1 text-lg font-bold text-zinc-900">{value}</p>
    </div>
  );
};

function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 B";
  const units = ["B", "KB", "MB", "GB", "TB"];
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${units[i]}`;
}

function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60_000) return `${(ms / 1000).toFixed(1)}s`;
  return `${(ms / 60_000).toFixed(1)}m`;
}
