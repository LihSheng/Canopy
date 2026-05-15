import Link from "next/link";
import { SummaryCard } from "./summary-card";
import { formatCurrency, formatPercent, getChangeColor } from "@/lib/formatters";
import type { DepartmentSummary } from "@/lib/api/types";

export function TopDepartmentsCard({
  departments,
  loading,
}: {
  departments: DepartmentSummary[];
  loading?: boolean;
}) {
  if (loading) {
    return (
      <SummaryCard title="Top Departments">
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-5 w-full animate-pulse rounded bg-zinc-100" />
          ))}
        </div>
      </SummaryCard>
    );
  }

  if (departments.length === 0) {
    return (
      <SummaryCard title="Top Departments">
        <p className="text-sm text-zinc-400">No data</p>
      </SummaryCard>
    );
  }

  return (
    <SummaryCard title="Top Departments">
      <ul className="divide-y divide-zinc-100">
        {departments.slice(0, 5).map((dept) => (
          <li key={dept.id} className="flex items-center justify-between py-2 first:pt-0 last:pb-0">
            <Link
              href={`/dashboard/departments/${dept.id}`}
              className="text-sm font-medium text-zinc-900 hover:text-zinc-600 transition-colors"
            >
              {dept.name}
            </Link>
            <div className="flex items-center gap-3">
              <span className="text-sm tabular-nums text-zinc-600">
                {formatCurrency(dept.total_spend)}
              </span>
              <span className={`text-xs font-medium tabular-nums ${getChangeColor(dept.change_pct)}`}>
                {formatPercent(dept.change_pct)}
              </span>
            </div>
          </li>
        ))}
      </ul>
    </SummaryCard>
  );
}
