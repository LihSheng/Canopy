"use client";

import { useState } from "react";
import type { DailyTrend } from "@/lib/api/admin-health";

interface TrendChartProps {
  data: DailyTrend[];
}

type MetricKey = "bytes_written" | "errors" | "sla_violations";

const METRIC_CONFIG: Record<
  MetricKey,
  { label: string; color: string; format: (v: number) => string }
> = {
  bytes_written: {
    label: "Bytes Written",
    color: "text-indigo-600",
    format: (v) => {
      if (v >= 1_000_000_000) return `${(v / 1_000_000_000).toFixed(1)}GB`;
      if (v >= 1_000_000) return `${(v / 1_000_000).toFixed(1)}MB`;
      if (v >= 1_000) return `${(v / 1_000).toFixed(1)}KB`;
      return `${v}B`;
    },
  },
  errors: {
    label: "Errors",
    color: "text-red-600",
    format: (v) => v.toString(),
  },
  sla_violations: {
    label: "SLA Violations",
    color: "text-amber-600",
    format: (v) => v.toString(),
  },
};

export const TrendChart = ({ data }: TrendChartProps) => {
  const [activeMetric, setActiveMetric] = useState<MetricKey>("errors");

  const config = METRIC_CONFIG[activeMetric];
  const values = data.map((d) => d[activeMetric]);
  const maxVal = Math.max(...values, 1);
  const chartHeight = 160;

  return (
    <div className="rounded-lg border border-zinc-200 bg-white">
      <div className="flex items-center justify-between border-b border-zinc-200 px-4 py-3">
        <h3 className="text-sm font-semibold text-zinc-900">
          Daily Trends (30d)
        </h3>
        <div className="flex gap-1">
          {(Object.keys(METRIC_CONFIG) as MetricKey[]).map((key) => (
            <button
              key={key}
              onClick={() => setActiveMetric(key)}
              className={`rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
                activeMetric === key
                  ? "bg-indigo-100 text-indigo-800"
                  : "text-zinc-500 hover:bg-zinc-100"
              }`}
            >
              {METRIC_CONFIG[key].label}
            </button>
          ))}
        </div>
      </div>
      <div className="px-4 py-4">
        <div className="relative" style={{ height: chartHeight }}>
          {/* Y-axis labels */}
          <div className="absolute -left-1 top-0 flex h-full flex-col justify-between text-xs text-zinc-400">
            <span>{config.format(maxVal)}</span>
            <span>{config.format(Math.round(maxVal / 2))}</span>
            <span>0</span>
          </div>
          {/* Bars */}
          <div className="ml-12 flex h-full items-end gap-[2px]">
            {data.map((d, _i) => {
              const val = d[activeMetric];
              const pct = maxVal > 0 ? (val / maxVal) * 100 : 0;
              return (
                <div
                  key={d.date}
                  className="group relative flex flex-1 flex-col justify-end"
                  style={{ height: "100%" }}
                >
                  <div
                    className={`w-full rounded-t transition-all hover:opacity-80 ${
                      activeMetric === "bytes_written"
                        ? "bg-indigo-500"
                        : activeMetric === "errors"
                          ? "bg-red-500"
                          : "bg-amber-500"
                    }`}
                    style={{ height: `${pct}%`, minHeight: val > 0 ? 2 : 0 }}
                    title={`${d.date}: ${config.format(val)}`}
                  />
                  {/* Tooltip on hover */}
                  <div className="absolute -top-6 left-1/2 hidden -translate-x-1/2 whitespace-nowrap rounded bg-zinc-800 px-2 py-1 text-xs text-white group-hover:block">
                    {d.date}: {config.format(val)}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
        {/* X-axis labels (every 5 days) */}
        <div className="ml-12 mt-2 flex justify-between text-xs text-zinc-400">
          {data
            .filter((_, i) => i % 5 === 0 || i === data.length - 1)
            .map((d) => (
              <span key={d.date}>{d.date.slice(5)}</span>
            ))}
        </div>
      </div>
    </div>
  );
};
