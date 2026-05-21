import { useMemo } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { formatCurrency } from "@/lib/formatters";
import type { TrendSeries } from "./dashboard-mappers";

type Props = {
  series: TrendSeries[];
};

const COLORS: Record<string, string> = {
  Total: "#111111",
  Payroll: "#8b5cf6",
  Claims: "#34d399",
};

export const DashboardTrendPanel = ({ series }: Props) => {
  const chartData = useMemo(() => {
    if (series.length === 0) return [];
    const months = series[0].data.map((d) => d.month);
    return months.map((month, i) => {
      const row: Record<string, string | number> = { month };
      for (const s of series) {
        row[s.label] = s.data[i]?.value ?? 0;
      }
      return row;
    });
  }, [series]);

  if (series.length === 0) {
    return (
      <div className="rounded-xl border border-zinc-200 bg-white p-5">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-zinc-400">
          Monthly Trends
        </h3>
        <div className="mt-4 flex h-48 items-center justify-center">
          <p className="text-sm text-zinc-400">No trend data available</p>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-zinc-200 bg-white p-5">
      <h3 className="text-xs font-semibold uppercase tracking-wider text-zinc-400">
        Monthly Trends
      </h3>
      <div className="mt-4 h-48">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 4, right: 4, bottom: 4, left: 4 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
            <XAxis
              dataKey="month"
              tick={{ fontSize: 11, fill: "#9ca3af" }}
              axisLine={{ stroke: "#e5e7eb" }}
              tickLine={false}
            />
            <YAxis
              tick={{ fontSize: 11, fill: "#9ca3af" }}
              axisLine={false}
              tickLine={false}
              tickFormatter={(v: number) => {
                if (v >= 1_000_000) return `${(v / 1_000_000).toFixed(1)}M`;
                if (v >= 1_000) return `${(v / 1_000).toFixed(0)}k`;
                return String(v);
              }}
            />
            <Tooltip
              contentStyle={{
                borderRadius: "8px",
                border: "1px solid #e5e7eb",
                boxShadow: "0 1px 2px rgba(0,0,0,0.05)",
                fontSize: "12px",
              }}
              formatter={(value) => [formatCurrency(Number(value)), ""]}
            />
            {series.map((s) => (
              <Line
                key={s.label}
                type="monotone"
                dataKey={s.label}
                stroke={COLORS[s.label] ?? "#6b7280"}
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 3, strokeWidth: 0 }}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
      <div className="mt-3 flex items-center justify-center gap-6">
        {series.map((s) => (
          <div key={s.label} className="flex items-center gap-1.5">
            <span
              className="h-2.5 w-2.5 rounded-full"
              style={{ backgroundColor: COLORS[s.label] ?? "#6b7280" }}
            />
            <span className="text-xs text-zinc-500">{s.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export const DashboardTrendPanelSkeleton = () => {
  return (
    <div className="rounded-xl border border-zinc-200 bg-white p-5">
      <div className="h-3 w-28 animate-pulse rounded bg-zinc-100" />
      <div className="mt-4 h-48 animate-pulse rounded bg-zinc-50" />
    </div>
  );
}
