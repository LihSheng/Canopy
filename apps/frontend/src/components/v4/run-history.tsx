"use client";

import Link from "next/link";
import type { Run } from "@/lib/api/types";

const statusStyles: Record<string, string> = {
  completed: "bg-green-100 text-green-800",
  failed: "bg-red-100 text-red-800",
  running: "bg-blue-100 text-blue-800",
  queued: "bg-zinc-100 text-zinc-600",
};

function formatDuration(ms: number | null): string {
  if (ms === null) return "--";
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  const min = Math.floor(ms / 60000);
  const sec = Math.round((ms % 60000) / 1000);
  return `${min}m ${sec}s`;
}

type Props = {
  runs: Run[];
  datasetId?: string;
};

export function RunHistory({ runs, datasetId }: Props) {
  if (runs.length === 0) {
    return (
      <div className="flex items-center justify-center py-12 text-sm text-zinc-500">
        No runs yet
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-lg border border-zinc-200">
      <table className="min-w-full divide-y divide-zinc-200 text-sm">
        <thead>
          <tr className="bg-zinc-50">
            <th className="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wider text-zinc-500">
              Status
            </th>
            <th className="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wider text-zinc-500">
              Started
            </th>
            <th className="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wider text-zinc-500">
              Duration
            </th>
            <th className="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wider text-zinc-500">
              Warnings
            </th>
            <th className="px-4 py-2" />
          </tr>
        </thead>
        <tbody className="divide-y divide-zinc-100">
          {runs.map((run) => (
            <tr key={run.id} className="hover:bg-zinc-50">
              <td className="px-4 py-2">
                <span
                  className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${
                    statusStyles[run.status] || "bg-zinc-100 text-zinc-600"
                  }`}
                >
                  {run.status}
                </span>
              </td>
              <td className="px-4 py-2 text-zinc-700">
                {run.started_at
                  ? new Date(run.started_at).toLocaleString()
                  : "Not started"}
              </td>
              <td className="px-4 py-2 text-zinc-700">
                {formatDuration(run.duration_ms)}
              </td>
              <td className="px-4 py-2 text-zinc-700">
                {run.warning_count > 0 ? (
                  <span className="font-medium text-amber-600">
                    {run.warning_count}
                  </span>
                ) : (
                  <span className="text-zinc-400">0</span>
                )}
              </td>
              <td className="px-4 py-2 text-right">
                <Link
                  href={`/dashboard/connections/runs/${run.id}`}
                  className="text-xs font-medium text-indigo-600 hover:text-indigo-500"
                >
                  View
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
