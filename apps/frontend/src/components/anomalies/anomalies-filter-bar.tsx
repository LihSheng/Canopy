"use client";

import type { TimeRangeKey } from "@/lib/navigation/time-range";

type Props = {
  timeRange: TimeRangeKey;
  severity: "high" | "medium" | "low" | null;
  departmentId?: string;
  onTimeRangeChange: (tr: TimeRangeKey) => void;
  onSeverityChange: (s: "high" | "medium" | "low" | null) => void;
};

const TIME_RANGE_OPTIONS: { key: TimeRangeKey; label: string }[] = [
  { key: "this_month", label: "This month" },
  { key: "last_3_months", label: "Last 3 months" },
  { key: "last_12_months", label: "Last 12 months" },
];

const SEVERITY_OPTIONS: { key: "high" | "medium" | "low" | null; label: string }[] = [
  { key: null, label: "All" },
  { key: "high", label: "High" },
  { key: "medium", label: "Medium" },
  { key: "low", label: "Low" },
];

export const AnomaliesFilterBar = ({
  timeRange,
  severity,
  departmentId,
  onTimeRangeChange,
  onSeverityChange,
}: Props) => {
  return (
    <div className="flex flex-wrap items-center gap-3">
      {departmentId && (
        <span className="inline-flex items-center gap-1 rounded-full border border-zinc-200 bg-zinc-50 px-2.5 py-1 text-xs font-medium text-zinc-600">
          Department filter active
        </span>
      )}
      <div className="flex items-center gap-2 text-sm">
        <span className="text-xs font-medium text-zinc-400">Range:</span>
        <div className="flex rounded-lg border border-zinc-200 bg-zinc-50 p-0.5">
          {TIME_RANGE_OPTIONS.map((opt) => (
            <button
              key={opt.key}
              onClick={() => onTimeRangeChange(opt.key)}
              className={`rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
                timeRange === opt.key
                  ? "bg-white text-zinc-900 shadow-sm"
                  : "text-zinc-500 hover:text-zinc-700"
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>
      <div className="flex items-center gap-2 text-sm">
        <span className="text-xs font-medium text-zinc-400">Severity:</span>
        <div className="flex rounded-lg border border-zinc-200 bg-zinc-50 p-0.5">
          {SEVERITY_OPTIONS.map((opt) => (
            <button
              key={opt.key ?? "all"}
              onClick={() => onSeverityChange(opt.key)}
              className={`rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
                severity === opt.key
                  ? "bg-white text-zinc-900 shadow-sm"
                  : "text-zinc-500 hover:text-zinc-700"
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
