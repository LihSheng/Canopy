"use client";

import type { TimeRangeKey } from "@/lib/navigation/time-range";
import type { SortKey } from "./department-list-mappers";
import { SORT_LABELS } from "./department-list-mappers";

type Props = {
  search: string;
  attentionOnly: boolean;
  timeRange: TimeRangeKey;
  activeSort: SortKey;
  onSearchChange: (v: string) => void;
  onAttentionOnlyChange: (v: boolean) => void;
  onTimeRangeChange: (tr: TimeRangeKey) => void;
  onSortChange: (s: SortKey) => void;
};

const TIME_RANGE_OPTIONS: { key: TimeRangeKey; label: string }[] = [
  { key: "this_month", label: "This month" },
  { key: "last_3_months", label: "Last 3 months" },
  { key: "last_12_months", label: "Last 12 months" },
];

const SORT_OPTIONS: SortKey[] = ["attention", "total_spend", "change_percent"];

export const DepartmentsFilterBar = ({
  search,
  attentionOnly,
  timeRange,
  activeSort,
  onSearchChange,
  onAttentionOnlyChange,
  onTimeRangeChange,
  onSortChange,
}: Props) => {
  return (
    <div className="flex flex-wrap items-center gap-3">
      <div className="relative">
        <svg
          viewBox="0 0 20 20"
          fill="currentColor"
          className="pointer-events-none absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-400"
        >
          <path
            fillRule="evenodd"
            d="M9 3.5a5.5 5.5 0 100 11 5.5 5.5 0 000-11zM2 9a7 7 0 1112.452 4.391l3.328 3.329a.75.75 0 11-1.06 1.06l-3.329-3.328A7 7 0 012 9z"
            clipRule="evenodd"
          />
        </svg>
        <input
          type="text"
          placeholder="Search departments..."
          value={search}
          onChange={(e) => onSearchChange(e.target.value)}
          className="h-9 w-48 rounded-lg border border-zinc-200 bg-white pl-8 pr-3 text-sm text-zinc-900 placeholder:text-zinc-400 focus:border-zinc-300 focus:outline-none focus:ring-0"
        />
      </div>

      <button
        onClick={() => onAttentionOnlyChange(!attentionOnly)}
        className={`inline-flex items-center gap-1.5 rounded-lg border px-2.5 py-1.5 text-xs font-medium transition-colors ${
          attentionOnly
            ? "border-zinc-300 bg-zinc-100 text-zinc-900"
            : "border-zinc-200 text-zinc-500 hover:border-zinc-300 hover:text-zinc-700"
        }`}
      >
        <svg viewBox="0 0 20 20" fill="currentColor" className="h-3.5 w-3.5">
          <path
            fillRule="evenodd"
            d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.17 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 2.495zM10 5a.75.75 0 01.75.75v3.5a.75.75 0 01-1.5 0v-3.5A.75.75 0 0110 5zm0 9a1 1 0 100-2 1 1 0 000 2z"
            clipRule="evenodd"
          />
        </svg>
        Attention only
      </button>

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
        <span className="text-xs font-medium text-zinc-400">Sort:</span>
        <div className="flex rounded-lg border border-zinc-200 bg-zinc-50 p-0.5">
          {SORT_OPTIONS.map((opt) => (
            <button
              key={opt}
              onClick={() => onSortChange(opt)}
              className={`rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
                activeSort === opt
                  ? "bg-white text-zinc-900 shadow-sm"
                  : "text-zinc-500 hover:text-zinc-700"
              }`}
            >
              {SORT_LABELS[opt]}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
