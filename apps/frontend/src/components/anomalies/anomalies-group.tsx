"use client";

import { useState } from "react";
import { AnomalyRow } from "./anomaly-row";
import type { TimeRangeKey } from "@/lib/navigation/time-range";
import type { AnomalyGroup } from "./anomaly-mappers";

type Props = {
  group: AnomalyGroup;
  timeRange: TimeRangeKey;
  expandedByDefault: boolean;
};

const SEVERITY_LABELS: Record<string, string> = {
  high: "High severity",
  medium: "Medium severity",
  low: "Low severity",
};

export const AnomaliesGroup = ({ group, timeRange, expandedByDefault }: Props) => {
  const [expanded, setExpanded] = useState(expandedByDefault);

  return (
    <div className="rounded-xl border border-zinc-200 bg-white">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center justify-between px-5 py-3.5 text-left"
        aria-expanded={expanded}
      >
        <div className="flex items-center gap-2.5">
          <svg
            viewBox="0 0 20 20"
            fill="currentColor"
            className={`h-4 w-4 text-zinc-400 transition-transform ${expanded ? "rotate-90" : ""}`}
          >
            <path
              fillRule="evenodd"
              d="M7.21 14.77a.75.75 0 01.02-1.06L11.168 10 7.23 6.29a.75.75 0 111.04-1.08l4.5 4.25a.75.75 0 010 1.08l-4.5 4.25a.75.75 0 01-1.06-.02z"
              clipRule="evenodd"
            />
          </svg>
          <h2 className="text-sm font-semibold tracking-tight text-zinc-900">
            {SEVERITY_LABELS[group.severity] ?? group.severity}
          </h2>
          <span className="rounded-full bg-zinc-100 px-2 py-0.5 text-xs font-medium tabular-nums text-zinc-500">
            {group.count}
          </span>
        </div>
      </button>
      {expanded && (
        <div className="divide-y divide-zinc-100 border-t border-zinc-100">
          {group.items.map((item) => (
            <AnomalyRow key={item.id} item={item} timeRange={timeRange} />
          ))}
        </div>
      )}
    </div>
  );
}
