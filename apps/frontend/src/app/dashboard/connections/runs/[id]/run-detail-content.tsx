"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { fetchRun } from "@/lib/api/data-source";
import type { Run } from "@/lib/api/types";
import { LoadingSpinner } from "@/components/shared/loading-spinner";
import { ErrorState } from "@/components/shared/error-state";
import { STATUS_COLORS, ROUTES, errorMessageFailedToLoad } from "@/lib/constants";

const formatDuration = (ms: number | null): string => {
  if (ms === null) return "N/A";
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  const min = Math.floor(ms / 60000);
  const sec = Math.round((ms % 60000) / 1000);
  return `${min}m ${sec}s`;
}

type Props = {
  runId: string;
};

const RunDetailContent = ({ runId }: Props) => {
  const [run, setRun] = useState<Run | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [retryKey, setRetryKey] = useState(0);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const data = await fetchRun(runId);
        if (!cancelled) setRun(data);
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : errorMessageFailedToLoad("run"));
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [runId, retryKey]);

  const retry = useCallback(() => setRetryKey((k) => k + 1), []);

  if (loading) return <LoadingSpinner text="Loading run details..." />;
  if (error) return <ErrorState message={error} onRetry={retry} />;
  if (!run) return <ErrorState message="Run not found" />;

  const progress = run.status === "completed" ? 100 : run.status === "failed" ? 100 : run.status === "running" ? 60 : 0;
  const progressColor = run.status === "failed" ? "bg-red-500" : run.status === "completed" ? "bg-green-500" : run.status === "running" ? "bg-blue-500" : "bg-zinc-300";

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div className="rounded-lg border border-zinc-200 bg-white p-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-zinc-900">Run {run.id.slice(0, 8)}</h2>
            <span
              className={`mt-1 inline-block rounded-full px-2.5 py-0.5 text-xs font-medium ${
                STATUS_COLORS[run.status] || "bg-zinc-100 text-zinc-600"
              }`}
            >
              {run.status}
            </span>
          </div>
          {run.dataset_id && (
            <Link
              href={ROUTES.connections.datasetDetail(run.dataset_id)}
              className="text-sm font-medium text-indigo-600 hover:text-indigo-500"
            >
              View Dataset
            </Link>
          )}
        </div>

        <div className="mt-6">
          <div className="mb-1 flex items-center justify-between text-xs text-zinc-500">
            <span>Progress</span>
            <span>{progress}%</span>
          </div>
          <div className="h-2 w-full overflow-hidden rounded-full bg-zinc-100">
            <div
              className={`h-full rounded-full transition-all duration-500 ${progressColor}`}
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      </div>

      <div className="rounded-lg border border-zinc-200 bg-white p-6">
        <h3 className="text-sm font-semibold text-zinc-900">Details</h3>
        <dl className="mt-4 space-y-3 text-sm">
          <DetailRow label="Started" value={run.started_at ? new Date(run.started_at).toLocaleString() : "Not started"} />
          <DetailRow label="Finished" value={run.finished_at ? new Date(run.finished_at).toLocaleString() : "N/A"} />
          <DetailRow label="Duration" value={formatDuration(run.duration_ms)} />
          <DetailRow label="Started By" value={run.started_by || "System"} />
          <DetailRow label="Warning Count" value={run.warning_count.toString()} />
          <DetailRow label="Error" value={run.error_message || "None"} isError={!!run.error_message} />
        </dl>
      </div>

      {run.warning_count > 0 && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-4">
          <h3 className="text-sm font-semibold text-amber-800">
            Warnings ({run.warning_count})
          </h3>
          <p className="mt-1 text-sm text-amber-700">
            This run completed with {run.warning_count} warning{run.warning_count !== 1 ? "s" : ""}.
            Check the dataset details for more information.
          </p>
        </div>
      )}

      {run.error_message && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4">
          <h3 className="text-sm font-semibold text-red-800">Error</h3>
          <pre className="mt-1 overflow-x-auto whitespace-pre-wrap text-sm text-red-700">
            {run.error_message}
          </pre>
        </div>
      )}
    </div>
  );
}
export default RunDetailContent;

const DetailRow = ({
  label,
  value,
  isError,
}: {
  label: string;
  value: string;
  isError?: boolean;
}) => {
  return (
    <div className="flex justify-between">
      <dt className="text-zinc-500">{label}</dt>
      <dd className={isError ? "font-medium text-red-600" : "text-zinc-900"}>
        {value}
      </dd>
    </div>
  );
}
