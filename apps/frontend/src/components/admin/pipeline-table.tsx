"use client";

import type { PipelineSummary } from "@/lib/api/admin-health";

interface PipelineTableProps {
  pipelines: PipelineSummary[];
  healthFilter?: string;
  onHealthFilterChange: (filter: string | undefined) => void;
  onPipelineClick: (pipelineId: string) => void;
}

const HEALTH_COLORS: Record<string, string> = {
  healthy: "bg-green-100 text-green-800",
  degraded: "bg-amber-100 text-amber-800",
  failed: "bg-red-100 text-red-800",
};

const FILTERS = [
  { value: undefined, label: "All" },
  { value: "healthy", label: "Healthy" },
  { value: "degraded", label: "Degraded" },
  { value: "failed", label: "Failed" },
];

export const PipelineTable = ({
  pipelines,
  healthFilter,
  onHealthFilterChange,
  onPipelineClick,
}: PipelineTableProps) => {
  return (
    <div className="rounded-lg border border-zinc-200 bg-white">
      <div className="flex items-center justify-between border-b border-zinc-200 px-4 py-3">
        <h3 className="text-sm font-semibold text-zinc-900">Pipelines</h3>
        <div className="flex gap-1">
          {FILTERS.map((f) => (
            <button
              key={f.label}
              onClick={() => onHealthFilterChange(f.value)}
              className={`rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
                healthFilter === f.value
                  ? "bg-indigo-100 text-indigo-800"
                  : "text-zinc-500 hover:bg-zinc-100"
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-zinc-200">
          <thead className="bg-zinc-50">
            <tr>
              <th className="px-4 py-2 text-left text-xs font-medium uppercase tracking-wider text-zinc-500">
                Pipeline
              </th>
              <th className="px-4 py-2 text-left text-xs font-medium uppercase tracking-wider text-zinc-500">
                Health
              </th>
              <th className="px-4 py-2 text-right text-xs font-medium uppercase tracking-wider text-zinc-500">
                Runs
              </th>
              <th className="px-4 py-2 text-right text-xs font-medium uppercase tracking-wider text-zinc-500">
                Failures
              </th>
              <th className="px-4 py-2 text-right text-xs font-medium uppercase tracking-wider text-zinc-500">
                Bytes Written
              </th>
              <th className="px-4 py-2 text-right text-xs font-medium uppercase tracking-wider text-zinc-500">
                SLA Violations
              </th>
              <th className="px-4 py-2 text-right text-xs font-medium uppercase tracking-wider text-zinc-500">
                Max Duration
              </th>
              <th className="px-4 py-2 text-left text-xs font-medium uppercase tracking-wider text-zinc-500">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-200">
            {pipelines.length === 0 ? (
              <tr>
                <td
                  colSpan={8}
                  className="px-4 py-8 text-center text-sm text-zinc-500"
                >
                  No pipelines found
                </td>
              </tr>
            ) : (
              pipelines.map((p) => (
                <tr key={p.pipeline_id} className="hover:bg-zinc-50">
                  <td className="whitespace-nowrap px-4 py-2 text-sm font-medium text-zinc-900">
                    {p.pipeline_id}
                  </td>
                  <td className="whitespace-nowrap px-4 py-2">
                    <span
                      className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${
                        HEALTH_COLORS[p.health]
                      }`}
                    >
                      {p.health}
                    </span>
                  </td>
                  <td className="whitespace-nowrap px-4 py-2 text-right text-sm text-zinc-900">
                    {p.total_runs}
                  </td>
                  <td className="whitespace-nowrap px-4 py-2 text-right text-sm text-zinc-900">
                    {p.total_failures}
                  </td>
                  <td className="whitespace-nowrap px-4 py-2 text-right text-sm text-zinc-900">
                    {formatBytes(p.total_bytes_written)}
                  </td>
                  <td className="whitespace-nowrap px-4 py-2 text-right text-sm text-zinc-900">
                    {p.total_sla_violations}
                  </td>
                  <td className="whitespace-nowrap px-4 py-2 text-right text-sm text-zinc-500">
                    {formatDuration(p.max_duration_ms)}
                  </td>
                  <td className="whitespace-nowrap px-4 py-2 text-sm">
                    <button
                      onClick={() => onPipelineClick(p.pipeline_id)}
                      className="font-medium text-indigo-600 hover:text-indigo-800"
                    >
                      Details
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
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
