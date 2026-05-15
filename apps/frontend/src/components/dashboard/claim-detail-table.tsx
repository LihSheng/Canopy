import { formatCurrency } from "@/lib/formatters";
import type { ClaimDetail } from "@/lib/api/types";

export function ClaimDetailTable({
  data,
  loading,
}: {
  data: ClaimDetail[];
  loading?: boolean;
}) {
  if (loading) {
    return (
      <div className="overflow-hidden rounded-xl border border-zinc-200 bg-white">
        <div className="border-b border-zinc-100 px-6 py-3">
          <div className="h-4 w-28 animate-pulse rounded bg-zinc-100" />
        </div>
        <div className="space-y-1 p-6">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="flex gap-4">
              {Array.from({ length: 5 }).map((_, j) => (
                <div key={j} className="h-4 flex-1 animate-pulse rounded bg-zinc-100" />
              ))}
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className="rounded-xl border border-zinc-200 bg-white p-6">
        <h3 className="text-xs font-medium uppercase tracking-wider text-zinc-500">
          Claim Details
        </h3>
        <p className="mt-4 text-sm text-zinc-400">No claims found</p>
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-xl border border-zinc-200 bg-white">
      <div className="border-b border-zinc-100 px-6 py-3">
        <h3 className="text-xs font-medium uppercase tracking-wider text-zinc-500">
          Claim Details
        </h3>
      </div>
      <table className="w-full">
        <thead>
          <tr className="border-b border-zinc-100 bg-zinc-50 text-left text-xs font-medium text-zinc-500">
            <th className="px-6 py-2.5">Employee</th>
            <th className="px-6 py-2.5">Type</th>
            <th className="px-6 py-2.5">Date</th>
            <th className="px-6 py-2.5 text-right">Amount</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-zinc-50">
          {data.map((claim) => (
            <tr key={claim.id} className="hover:bg-zinc-50 transition-colors">
              <td className="px-6 py-2.5 text-sm font-medium text-zinc-900">
                {claim.employee_name}
              </td>
              <td className="px-6 py-2.5 text-sm text-zinc-600">{claim.type}</td>
              <td className="px-6 py-2.5 text-sm tabular-nums text-zinc-500">
                {claim.date}
              </td>
              <td className="px-6 py-2.5 text-right text-sm font-medium tabular-nums text-zinc-900">
                {formatCurrency(claim.amount)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
