"use client";

import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { TrendChartData } from "@/lib/mappers";

export const MonthlyTrendChart = ({
  data,
  loading,
}: {
  data: TrendChartData[];
  loading?: boolean;
}) => {
  if (loading) {
    return <ChartSkeleton />;
  }

  if (data.length === 0) {
    return <ChartEmpty />;
  }

  return (
    <div className="rounded-xl border border-zinc-200 bg-white p-6">
      <h3 className="text-xs font-medium uppercase tracking-wider text-zinc-500">
        Monthly Spend Trend
      </h3>
      <div className="mt-4 h-72">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
            <XAxis
              dataKey="month"
              tick={{ fontSize: 12, fill: "#6b7280" }}
              axisLine={{ stroke: "#e5e7eb" }}
              tickLine={false}
            />
            <YAxis
              tick={{ fontSize: 12, fill: "#6b7280" }}
              axisLine={{ stroke: "#e5e7eb" }}
              tickLine={false}
              tickFormatter={(v: number) =>
                v >= 1000000 ? `${(v / 1000000).toFixed(1)}M` : `${(v / 1000).toFixed(0)}K`
              }
            />
            <Tooltip
              contentStyle={{
                borderRadius: "8px",
                border: "1px solid #e5e7eb",
                boxShadow: "0 1px 3px rgba(0,0,0,0.08)",
                fontSize: "13px",
              }}
              formatter={(value) =>
                new Intl.NumberFormat("en-US", {
                  style: "currency",
                  currency: "USD",
                  minimumFractionDigits: 0,
                }).format(Number(value))
              }
            />
            <Legend
              wrapperStyle={{ fontSize: "12px", color: "#6b7280" }}
            />
            <Line
              type="monotone"
              dataKey="Total"
              stroke="#111111"
              strokeWidth={2}
              dot={{ r: 3, fill: "#111111" }}
            />
            <Line
              type="monotone"
              dataKey="Payroll"
              stroke="#3b82f6"
              strokeWidth={1.5}
              dot={{ r: 2, fill: "#3b82f6" }}
            />
            <Line
              type="monotone"
              dataKey="Claims"
              stroke="#f59e0b"
              strokeWidth={1.5}
              dot={{ r: 2, fill: "#f59e0b" }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

const ChartSkeleton = () => {
  return (
    <div className="rounded-xl border border-zinc-200 bg-white p-6">
      <div className="h-4 w-32 animate-pulse rounded bg-zinc-100" />
      <div className="mt-4 h-72 animate-pulse rounded bg-zinc-50" />
    </div>
  );
}

const ChartEmpty = () => {
  return (
    <div className="rounded-xl border border-zinc-200 bg-white p-6">
      <h3 className="text-xs font-medium uppercase tracking-wider text-zinc-500">
        Monthly Spend Trend
      </h3>
      <p className="mt-4 text-sm text-zinc-400">No trend data available</p>
    </div>
  );
}
