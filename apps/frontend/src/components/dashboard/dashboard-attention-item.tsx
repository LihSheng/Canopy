import Link from "next/link";
import { formatPercent, getSeverityColor, getChangeBgColor } from "@/lib/formatters";
import { buildDashboardToDepartmentDetailLink } from "@/lib/navigation/dashboard-links";
import type { TimeRangeKey } from "@/lib/navigation/time-range";
import type { AttentionListItem } from "./dashboard-mappers";

type Props = {
  item: AttentionListItem;
  timeRange: TimeRangeKey;
};

export function DashboardAttentionItem({ item, timeRange }: Props) {
  const detailLink = buildDashboardToDepartmentDetailLink(
    item.departmentId,
    timeRange,
    "dashboard_attention",
  );

  return (
    <Link
      href={detailLink}
      className="flex items-center gap-4 rounded-lg px-4 py-3 transition-colors hover:bg-zinc-50"
    >
      <span
        className={`inline-flex shrink-0 rounded-full border px-2 py-0.5 text-xs font-medium ${getSeverityColor(item.severity)}`}
      >
        {item.severity}
      </span>
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium text-zinc-900">
          {item.departmentName}
        </p>
        <p className="truncate text-xs text-zinc-500">{item.reason}</p>
      </div>
      <span
        className={`inline-flex shrink-0 items-center rounded-full px-2 py-0.5 text-xs font-semibold tabular-nums ${getChangeBgColor(item.changePct)}`}
      >
        {formatPercent(item.changePct)}
      </span>
    </Link>
  );
}
