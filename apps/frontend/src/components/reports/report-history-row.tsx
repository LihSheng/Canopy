"use client";

import { useState } from "react";
import { TIME_RANGE_LABELS } from "@/lib/navigation/time-range";
import type { ExportHistoryItem } from "./report-mappers";

const STATUS_COLORS: Record<ExportHistoryItem["status"], string> = {
  queued: "bg-zinc-100 text-zinc-600",
  running: "bg-blue-100 text-blue-700",
  completed: "bg-emerald-100 text-emerald-700",
  failed: "bg-red-100 text-red-700",
};

const STATUS_LABELS: Record<ExportHistoryItem["status"], string> = {
  queued: "Queued",
  running: "Running",
  completed: "Completed",
  failed: "Failed",
};

export const ReportHistoryRow = ({
  item,
  onRerun,
  exporting,
}: {
  item: ExportHistoryItem;
  onRerun: (id: string) => void;
  exporting: string | null;
}) => {
  const [showDetails, setShowDetails] = useState(false);

  const timeLabel = TIME_RANGE_LABELS[item.timeRange] ?? item.timeRange;
  const createdAt = item.createdAt
    ? new Date(item.createdAt).toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      })
    : null;

  return (
    <div className="rounded-lg border border-zinc-200 bg-white p-4">
      <div className="flex items-center justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold text-zinc-900">{item.presetName}</span>
            <span
              className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_COLORS[item.status]}`}
            >
              {STATUS_LABELS[item.status]}
            </span>
          </div>
          <div className="mt-1 flex items-center gap-3 text-xs text-zinc-500">
            {createdAt && <span>{createdAt}</span>}
            <span>{timeLabel}</span>
            {item.snapshotTimestamp && (
              <span>
                Snapshot:{" "}
                {new Date(item.snapshotTimestamp).toLocaleDateString("en-US", {
                  month: "short",
                  day: "numeric",
                })}
              </span>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          {item.status === "running" && (
            <svg
              className="h-4 w-4 animate-spin text-blue-500"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
          )}

          {item.status === "completed" && (
            <>
              <a
                href={`${process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8005"}${item.downloadUrl}`}
                className="rounded-lg bg-zinc-900 px-3 py-1.5 text-xs font-semibold text-white transition-colors hover:bg-zinc-800"
              >
                Download
              </a>
              <button
                onClick={() => onRerun(item.id)}
                disabled={exporting === item.id}
                className="rounded-lg border border-zinc-200 bg-white px-3 py-1.5 text-xs font-semibold text-zinc-700 transition-colors hover:bg-zinc-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Run again
              </button>
            </>
          )}

          {item.status === "failed" && (
            <button
              onClick={() => setShowDetails(!showDetails)}
              className="rounded-lg border border-red-200 bg-red-50 px-3 py-1.5 text-xs font-semibold text-red-700 transition-colors hover:bg-red-100"
            >
              {showDetails ? "Hide details" : "View details"}
            </button>
          )}
        </div>
      </div>

      {item.status === "failed" && showDetails && item.errorSummary && (
        <div className="mt-3 rounded-md bg-red-50 border border-red-100 p-3">
          <p className="text-xs font-medium text-red-800">Error details</p>
          <p className="mt-1 text-xs text-red-700">{item.errorSummary}</p>
        </div>
      )}
    </div>
  );
}
