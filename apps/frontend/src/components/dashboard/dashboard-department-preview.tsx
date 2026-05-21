import Link from "next/link";
import { formatCurrency, formatPercent, getChangeBgColor, getSeverityColor } from "@/lib/formatters";
import { buildDashboardToDepartmentDetailLink } from "@/lib/navigation/links";
import type { TimeRangeKey } from "@/lib/navigation/time-range";
import type { DepartmentPreviewItem } from "./dashboard-mappers";

type Props = {
  departments: DepartmentPreviewItem[];
  timeRange: TimeRangeKey;
};

export const DashboardDepartmentPreview = ({ departments, timeRange }: Props) => {
  return (
    <div className="rounded-xl border border-zinc-200 bg-white">
      <div className="flex items-center justify-between border-b border-zinc-100 px-5 py-3.5">
        <h2 className="text-sm font-semibold tracking-tight text-zinc-900">
          Top Departments
        </h2>
      </div>
      {departments.length === 0 ? (
        <div className="px-5 py-8 text-center">
          <p className="text-sm text-zinc-500">No department data</p>
        </div>
      ) : (
        <div className="divide-y divide-zinc-100">
          {departments.map((dept) => (
            <Link
              key={dept.id}
              href={buildDashboardToDepartmentDetailLink(
                dept.id,
                timeRange,
                "dashboard_ranking",
              )}
              className="flex items-center gap-4 px-5 py-3 transition-colors hover:bg-zinc-50"
            >
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <p className="truncate text-sm font-medium text-zinc-900">
                    {dept.name}
                  </p>
                  {dept.attentionState && (
                    <span
                      className={`inline-flex shrink-0 rounded-full border px-2 py-0.5 text-[10px] font-medium ${getSeverityColor(dept.attentionState as "high" | "medium" | "low")}`}
                    >
                      {dept.attentionState}
                    </span>
                  )}
                </div>
              </div>
              <span className="text-sm font-semibold tabular-nums text-zinc-900">
                {formatCurrency(dept.totalSpend)}
              </span>
              <span
                className={`inline-flex shrink-0 items-center rounded-full px-2 py-0.5 text-xs font-semibold tabular-nums ${getChangeBgColor(dept.changePct)}`}
              >
                {formatPercent(dept.changePct)}
              </span>
            </Link>
          ))}
        </div>
      )}
      <div className="border-t border-zinc-100 px-5 py-2.5">
        <Link
          href="/dashboard/departments"
          className="text-xs font-medium text-zinc-500 transition-colors hover:text-zinc-900"
        >
          View all departments &rarr;
        </Link>
      </div>
    </div>
  );
}

export const DashboardDepartmentPreviewSkeleton = () => {
  return (
    <div className="rounded-xl border border-zinc-200 bg-white">
      <div className="flex items-center justify-between border-b border-zinc-100 px-5 py-3.5">
        <div className="h-4 w-32 animate-pulse rounded bg-zinc-100" />
      </div>
      <div className="divide-y divide-zinc-100">
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="flex items-center gap-4 px-5 py-3">
            <div className="flex-1">
              <div className="h-3.5 w-32 animate-pulse rounded bg-zinc-100" />
            </div>
            <div className="h-3.5 w-20 animate-pulse rounded bg-zinc-100" />
            <div className="h-5 w-14 animate-pulse rounded-full bg-zinc-100" />
          </div>
        ))}
      </div>
    </div>
  );
}
