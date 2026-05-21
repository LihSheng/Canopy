import { formatCurrency, formatPercent, getChangeBgColor, getSeverityColor } from "@/lib/formatters";
import type { TimeRangeKey } from "@/lib/navigation/time-range";
import { TIME_RANGE_LABELS } from "@/lib/navigation/time-range";

export type DetailSummary = {
  departmentName: string;
  attentionState: string | null;
  totalSpend: number;
  changePercent: number;
};

type Props = {
  summary: DetailSummary;
  timeRange: TimeRangeKey;
  onTimeRangeChange: (tr: TimeRangeKey) => void;
};

const TIME_RANGE_OPTIONS: { key: TimeRangeKey; label: string }[] = [
  { key: "this_month", label: "This month" },
  { key: "last_3_months", label: "Last 3 months" },
  { key: "last_12_months", label: "Last 12 months" },
];

export const DepartmentDetailHeader = ({ summary, timeRange, onTimeRangeChange }: Props) => {
  return (
    <header className="flex items-center justify-between border-b border-zinc-200 bg-white px-6 py-4">
      <div className="min-w-0">
        <div className="flex items-center gap-2.5">
          <h1 className="truncate text-lg font-semibold tracking-tight text-zinc-900">
            {summary.departmentName}
          </h1>
          {summary.attentionState && (
            <span
              className={`inline-flex shrink-0 rounded-full border px-2 py-0.5 text-[10px] font-medium ${getSeverityColor(
                summary.attentionState as "high" | "medium" | "low",
              )}`}
            >
              {summary.attentionState}
            </span>
          )}
        </div>
        <div className="mt-1 flex items-center gap-3">
          <p className="text-sm text-zinc-500">
            <span className="text-xs text-zinc-400">{TIME_RANGE_LABELS[timeRange]}</span>
          </p>
        </div>
      </div>
      <div className="flex items-center gap-4">
        <div className="hidden sm:flex items-center gap-1.5 rounded-lg border border-zinc-200 bg-zinc-50 p-0.5">
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
        <div className="text-right">
          <p className="text-2xl font-bold tabular-nums tracking-tight text-zinc-900">
            {formatCurrency(summary.totalSpend)}
          </p>
          <span
            className={`inline-flex shrink-0 items-center rounded-full px-2 py-0.5 text-xs font-semibold tabular-nums ${getChangeBgColor(summary.changePercent)}`}
          >
            {formatPercent(summary.changePercent)}
          </span>
        </div>
      </div>
    </header>
  );
}
