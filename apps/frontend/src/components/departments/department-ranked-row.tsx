import Link from "next/link";
import { formatCurrency, formatPercent, getChangeBgColor, getSeverityColor } from "@/lib/formatters";
import { buildDashboardToDepartmentDetailLink } from "@/lib/navigation/links";
import type { TimeRangeKey } from "@/lib/navigation/time-range";
import type { DepartmentRankingItem } from "./department-list-mappers";

type Props = {
  item: DepartmentRankingItem;
  timeRange: TimeRangeKey;
};

export function DepartmentRankedRow({ item, timeRange }: Props) {
  const detailLink = buildDashboardToDepartmentDetailLink(
    item.id,
    timeRange,
    "dashboard_ranking",
  );

  const hasAttention = item.attentionState !== null;

  return (
    <Link
      href={detailLink}
      className={`flex items-center gap-4 rounded-lg px-4 py-3 transition-colors hover:bg-zinc-50 ${
        hasAttention ? "bg-zinc-50/50" : ""
      }`}
    >
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <p
            className={`truncate text-sm ${
              hasAttention ? "font-semibold text-zinc-900" : "font-medium text-zinc-700"
            }`}
          >
            {item.name}
          </p>
          {item.attentionState && (
            <span
              className={`inline-flex shrink-0 rounded-full border px-2 py-0.5 text-[10px] font-semibold ${getSeverityColor(item.attentionState)}`}
            >
              {item.attentionState}
            </span>
          )}
        </div>
      </div>
      <span className="text-sm font-semibold tabular-nums text-zinc-900">
        {formatCurrency(item.totalSpend)}
      </span>
      <span
        className={`inline-flex shrink-0 items-center rounded-full px-2 py-0.5 text-xs font-semibold tabular-nums ${getChangeBgColor(item.changePct)}`}
      >
        {formatPercent(item.changePct)}
      </span>
    </Link>
  );
}
