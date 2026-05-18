import type { DatasetHealth } from "@/lib/api/types";

type Props = {
  health: DatasetHealth | null;
  versionCount: number;
  activeVersionNumber: number | undefined;
};

const statusColor: Record<string, string> = {
  completed: "bg-green-100 text-green-800",
  failed: "bg-red-100 text-red-800",
  running: "bg-blue-100 text-blue-800",
  queued: "bg-zinc-100 text-zinc-600",
};

function formatNumber(n: number): string {
  return n.toLocaleString();
}

export function DatasetSummaryCards({ health, versionCount, activeVersionNumber }: Props) {
  return (
    <div className="grid grid-cols-2 gap-4">
      <div className="rounded-lg border border-zinc-200 bg-white p-4">
        <span className="text-xs font-medium text-zinc-500">Row Count</span>
        <p className="mt-1 text-lg font-semibold text-zinc-900">
          {health ? formatNumber(health.row_count) : "--"}
        </p>
      </div>

      <div className="rounded-lg border border-zinc-200 bg-white p-4">
        <span className="text-xs font-medium text-zinc-500">Column Count</span>
        <p className="mt-1 text-lg font-semibold text-zinc-900">
          {health ? health.column_count : "--"}
        </p>
      </div>

      <div className="rounded-lg border border-zinc-200 bg-white p-4">
        <span className="text-xs font-medium text-zinc-500">Version</span>
        <p className="mt-1 text-lg font-semibold text-zinc-900">
          {activeVersionNumber !== undefined
            ? `v${activeVersionNumber} (of ${versionCount})`
            : "--"}
        </p>
      </div>

      <div className="rounded-lg border border-zinc-200 bg-white p-4">
        <span className="text-xs font-medium text-zinc-500">Last Run</span>
        <div className="mt-1">
          {health?.last_run_status ? (
            <>
              <span
                className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${
                  statusColor[health.last_run_status] || "bg-zinc-100 text-zinc-600"
                }`}
              >
                {health.last_run_status}
              </span>
              {health.freshness_at && (
                <p className="mt-1 text-xs text-zinc-500">
                  {new Date(health.freshness_at).toLocaleString()}
                </p>
              )}
            </>
          ) : (
            <span className="text-sm text-zinc-400">--</span>
          )}
        </div>
      </div>
    </div>
  );
}
