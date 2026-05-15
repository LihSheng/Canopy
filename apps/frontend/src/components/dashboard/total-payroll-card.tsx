import { SummaryCard } from "./summary-card";
import { formatCurrency } from "@/lib/formatters";

export function TotalPayrollCard({
  value,
  changePct,
  loading,
}: {
  value: number;
  changePct?: number;
  loading?: boolean;
}) {
  if (loading) {
    return (
      <SummaryCard title="Total Payroll">
        <div className="h-8 w-24 animate-pulse rounded bg-zinc-100" />
      </SummaryCard>
    );
  }

  return (
    <SummaryCard title="Total Payroll">
      <p className="text-2xl font-semibold tracking-tight text-zinc-900">
        {formatCurrency(value)}
      </p>
      {changePct !== undefined && (
        <p
          className={`mt-1 text-sm font-medium ${
            changePct > 0 ? "text-red-600" : changePct < 0 ? "text-emerald-600" : "text-zinc-500"
          }`}
        >
          {changePct > 0 ? "+" : ""}
          {changePct.toFixed(1)}% vs last month
        </p>
      )}
    </SummaryCard>
  );
}
