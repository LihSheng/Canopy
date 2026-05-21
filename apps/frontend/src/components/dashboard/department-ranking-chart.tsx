"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { DepartmentSummary } from "@/lib/api/types";

export const DepartmentRankingChart = ({
  data,
  loading,
}: {
  data: DepartmentSummary[];
  loading?: boolean;
}) => {
  if (loading) {
    return (
      <div className="rounded-xl border border-zinc-200 bg-white p-6">
        <div className="h-4 w-40 animate-pulse rounded bg-zinc-100" />
        <div className="mt-4 h-72 animate-pulse rounded bg-zinc-50" />
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className="rounded-xl border border-zinc-200 bg-white p-6">
        <h3 className="text-xs font-medium uppercase tracking-wider text-zinc-500">
          Department Spend
        </h3>
        <p className="mt-4 text-sm text-zinc-400">No department data available</p>
      </div>
    );
  }

  const chartData = [...data]
    .sort((a, b) => b.total_spend - a.total_spend)
    .slice(0, 10)
    .map((d) => ({
      name: d.name.length > 16 ? d.name.slice(0, 14) + "..." : d.name,
      Payroll: d.payroll_spend,
      Claims: d.claims_spend,
    }));

  return (
    <div className="rounded-xl border border-zinc-200 bg-white p-6">
      <h3 className="text-xs font-medium uppercase tracking-wider text-zinc-500">
        Department Spend
      </h3>
      <div className="mt-4 h-72">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
            <XAxis
              type="number"
              tick={{ fontSize: 12, fill: "#6b7280" }}
              axisLine={{ stroke: "#e5e7eb" }}
              tickLine={false}
              tickFormatter={(v: number) =>
                v >= 1000000 ? `${(v / 1000000).toFixed(1)}M` : `${(v / 1000).toFixed(0)}K`
              }
            />
            <YAxis
              type="category"
              dataKey="name"
              tick={{ fontSize: 12, fill: "#6b7280" }}
              axisLine={{ stroke: "#e5e7eb" }}
              tickLine={false}
              width={130}
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
            <Bar dataKey="Payroll" stackId="a" fill="#3b82f6" radius={[0, 0, 0, 0]} />
            <Bar dataKey="Claims" stackId="a" fill="#f59e0b" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
