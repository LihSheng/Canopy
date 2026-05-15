import { formatCurrency } from "@/lib/formatters";
import type { EmployeeContribution } from "@/lib/api/types";

export function EmployeeContributionTable({
  data,
  loading,
}: {
  data: EmployeeContribution[];
  loading?: boolean;
}) {
  if (loading) {
    return <TableSkeleton cols={4} rows={5} />;
  }

  if (data.length === 0) {
    return (
      <div className="rounded-xl border border-zinc-200 bg-white p-6">
        <h3 className="text-xs font-medium uppercase tracking-wider text-zinc-500">
          Employee Contributions
        </h3>
        <p className="mt-4 text-sm text-zinc-400">No employee data available</p>
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-xl border border-zinc-200 bg-white">
      <div className="border-b border-zinc-100 px-6 py-3">
        <h3 className="text-xs font-medium uppercase tracking-wider text-zinc-500">
          Employee Contributions
        </h3>
      </div>
      <table className="w-full">
        <thead>
          <tr className="border-b border-zinc-100 bg-zinc-50 text-left text-xs font-medium text-zinc-500">
            <th className="px-6 py-2.5">Name</th>
            <th className="px-6 py-2.5 text-right">Payroll</th>
            <th className="px-6 py-2.5 text-right">Claims</th>
            <th className="px-6 py-2.5 text-right">Total</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-zinc-50">
          {data.map((emp) => (
            <tr key={emp.id} className="hover:bg-zinc-50 transition-colors">
              <td className="px-6 py-2.5 text-sm font-medium text-zinc-900">
                {emp.name}
              </td>
              <td className="px-6 py-2.5 text-right text-sm tabular-nums text-zinc-600">
                {formatCurrency(emp.payroll)}
              </td>
              <td className="px-6 py-2.5 text-right text-sm tabular-nums text-zinc-600">
                {formatCurrency(emp.claims)}
              </td>
              <td className="px-6 py-2.5 text-right text-sm font-medium tabular-nums text-zinc-900">
                {formatCurrency(emp.total)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function TableSkeleton({ cols, rows }: { cols: number; rows: number }) {
  return (
    <div className="overflow-hidden rounded-xl border border-zinc-200 bg-white">
      <div className="border-b border-zinc-100 px-6 py-3">
        <div className="h-4 w-40 animate-pulse rounded bg-zinc-100" />
      </div>
      <div className="space-y-1 p-6">
        {Array.from({ length: rows }).map((_, i) => (
          <div key={i} className="flex gap-4">
            {Array.from({ length: cols }).map((_, j) => (
              <div
                key={j}
                className="h-4 flex-1 animate-pulse rounded bg-zinc-100"
              />
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}
