"use client";

import {
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import type { ClaimTypeBreakdown } from "@/lib/api/types";

const COLORS = ["#111111", "#3b82f6", "#f59e0b", "#10b981", "#8b5cf6", "#ec4899"];

export function ClaimTypeBreakdownChart({
  data,
  loading,
}: {
  data: ClaimTypeBreakdown[];
  loading?: boolean;
}) {
  if (loading) {
    return (
      <div className="rounded-xl border border-zinc-200 bg-white p-6">
        <div className="h-4 w-32 animate-pulse rounded bg-zinc-100" />
        <div className="mt-4 h-64 animate-pulse rounded bg-zinc-50" />
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className="rounded-xl border border-zinc-200 bg-white p-6">
        <h3 className="text-xs font-medium uppercase tracking-wider text-zinc-500">
          Claim Types
        </h3>
        <p className="mt-4 text-sm text-zinc-400">No claim data available</p>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-zinc-200 bg-white p-6">
      <h3 className="text-xs font-medium uppercase tracking-wider text-zinc-500">
        Claim Types
      </h3>
      <div className="mt-4 h-64">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              dataKey="amount"
              nameKey="type"
              cx="50%"
              cy="50%"
              outerRadius={80}
              innerRadius={50}
              paddingAngle={2}
            >
              {data.map((_, index) => (
                <Cell
                  key={index}
                  fill={COLORS[index % COLORS.length]}
                  stroke="none"
                />
              ))}
            </Pie>
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
          </PieChart>
        </ResponsiveContainer>
      </div>
      <div className="mt-3 flex flex-wrap gap-3">
        {data.map((item, index) => (
          <div key={item.type} className="flex items-center gap-1.5 text-xs text-zinc-600">
            <span
              className="inline-block h-2.5 w-2.5 rounded-full"
              style={{ backgroundColor: COLORS[index % COLORS.length] }}
            />
            {item.type}
          </div>
        ))}
      </div>
    </div>
  );
}
