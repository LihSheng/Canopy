"use client";

import Link from "next/link";
import type { RunDetail, FailureRun } from "@/lib/api/admin-health";
import { ROUTES } from "@/lib/constants";

interface RunDetailDrawerProps {
  runDetail: RunDetail | null;
  loading: boolean;
  onPipelineClick: (pipelineId: string) => void;
}

export const RunDetailDrawer = ({
  runDetail,
  loading,
  onPipelineClick,
}: RunDetailDrawerProps) => {
  if (loading) {
    return (
      <div className="flex min-h-48 items-center justify-center">
        <p className="text-sm text-zinc-500">Loading run detail...</p>
      </div>
    );
  }

  if (!runDetail) {
    return (
      <div className="flex min-h-48 items-center justify-center">
        <p className="text-sm text-zinc-500">Run not found</p>
      </div>
    );
  }

  const steps = runDetail.steps;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-zinc-900">Run Detail</h2>
        <p className="font-mono text-sm text-zinc-500">{runDetail.run_id}</p>
      </div>

      {/* Step Timeline */}
      <div className="rounded-lg border border-zinc-200 bg-white">
        <div className="border-b border-zinc-200 px-4 py-3">
          <h3 className="text-sm font-semibold text-zinc-900">
            Step Timeline ({steps.length} steps)
          </h3>
        </div>
        <div className="divide-y divide-zinc-100">
          {steps.length === 0 ? (
            <div className="px-4 py-8 text-center text-sm text-zinc-500">
              No telemetry steps recorded
            </div>
          ) : (
            steps.map((step, index) => (
              <StepRow
                key={step.id}
                step={step}
                index={index}
                onPipelineClick={onPipelineClick}
              />
            ))
          )}
        </div>
      </div>
    </div>
  );
};

const StepRow = ({
  step,
  index,
  onPipelineClick,
}: {
  step: FailureRun;
  index: number;
  onPipelineClick: (pipelineId: string) => void;
}) => {
  return (
    <div className="px-4 py-3">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2">
          <span className="flex h-6 w-6 items-center justify-center rounded-full bg-zinc-100 text-xs font-medium text-zinc-600">
            {index + 1}
          </span>
          <div>
            <p className="text-sm font-medium text-zinc-900">
              {step.pipeline_id}
              {step.job_type && (
                <span className="ml-2 text-xs text-zinc-400">
                  ({step.job_type})
                </span>
              )}
            </p>
            <button
              onClick={() => onPipelineClick(step.pipeline_id)}
              className="text-xs font-medium text-indigo-600 hover:text-indigo-800"
            >
              View Pipeline
            </button>
          </div>
        </div>
        <span
          className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${
            step.status === "failed"
              ? "bg-red-100 text-red-800"
              : step.status === "warning"
                ? "bg-amber-100 text-amber-800"
                : "bg-green-100 text-green-800"
          }`}
        >
          {step.status}
        </span>
      </div>

      {/* Error Message */}
      {step.error_message && (
        <div className="mt-2 rounded-md bg-red-50 px-3 py-2">
          <p className="text-xs font-medium text-red-800">Error:</p>
          <p className="mt-0.5 text-sm text-red-700">{step.error_message}</p>
        </div>
      )}

      {/* Warning Message */}
      {step.warning_message && (
        <div className="mt-2 rounded-md bg-amber-50 px-3 py-2">
          <p className="text-xs font-medium text-amber-800">Warning:</p>
          <p className="mt-0.5 text-sm text-amber-700">{step.warning_message}</p>
        </div>
      )}

      {/* Telemetry Fields */}
      <div className="mt-2 grid grid-cols-2 gap-x-4 gap-y-1 sm:grid-cols-4">
        <Field label="Duration" value={formatDuration(step.duration_ms)} />
        <Field label="Bytes Written" value={formatBytes(step.bytes_written)} />
        <Field label="Rows Processed" value={step.rows_processed.toLocaleString()} />
        <Field
          label="Latency Threshold"
          value={
            step.latency_threshold_ms != null
              ? formatDuration(step.latency_threshold_ms)
              : "-"
          }
        />
        <Field
          label="Started"
          value={
            step.started_at
              ? new Date(step.started_at).toLocaleString()
              : "-"
          }
        />
        <Field
          label="Finished"
          value={
            step.finished_at
              ? new Date(step.finished_at).toLocaleString()
              : "-"
          }
        />
        {step.dataset_id && (
          <div>
            <p className="text-xs text-zinc-500">Dataset ID</p>
            <Link
              href={ROUTES.connections.datasetLineage(step.dataset_id)}
              className="text-sm font-medium text-indigo-600 hover:text-indigo-800"
            >
              {step.dataset_id}
            </Link>
          </div>
        )}
        {step.connection_id && (
          <div>
            <p className="text-xs text-zinc-500">Connection ID</p>
            <Link
              href={ROUTES.connections.connectionLineage(step.connection_id)}
              className="text-sm font-medium text-indigo-600 hover:text-indigo-800"
            >
              {step.connection_id}
            </Link>
          </div>
        )}
      </div>
    </div>
  );
};

const Field = ({ label, value }: { label: string; value: string }) => (
  <div>
    <p className="text-xs text-zinc-500">{label}</p>
    <p className="text-sm text-zinc-900">{value}</p>
  </div>
);

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
