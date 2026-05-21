import Link from "next/link";
import { DashboardAttentionItem } from "./dashboard-attention-item";
import { buildDashboardToAnomaliesLink } from "@/lib/navigation/links";
import type { TimeRangeKey } from "@/lib/navigation/time-range";
import type { AttentionListItem } from "./dashboard-mappers";

type Props = {
  items: AttentionListItem[];
  timeRange: TimeRangeKey;
};

export function DashboardAttentionPanel({ items, timeRange }: Props) {
  const viewAllLink = buildDashboardToAnomaliesLink(timeRange);

  return (
    <div className="rounded-xl border border-zinc-200 bg-white">
      <div className="flex items-center justify-between border-b border-zinc-100 px-5 py-3.5">
        <h2 className="text-sm font-semibold tracking-tight text-zinc-900">
          Top Attention Items
        </h2>
      </div>
      {items.length === 0 ? (
        <div className="px-5 py-8 text-center">
          <p className="text-sm text-zinc-500">No attention items</p>
          <p className="mt-1 text-xs text-zinc-400">
            All departments are within expected ranges.
          </p>
        </div>
      ) : (
        <div className="divide-y divide-zinc-100">
          {items.map((item) => (
            <DashboardAttentionItem key={item.id} item={item} timeRange={timeRange} />
          ))}
        </div>
      )}
      <div className="border-t border-zinc-100 px-5 py-2.5">
        <Link
          href={viewAllLink}
          className="text-xs font-medium text-zinc-500 transition-colors hover:text-zinc-900"
        >
          View all anomalies &rarr;
        </Link>
      </div>
    </div>
  );
}

export function DashboardAttentionPanelSkeleton() {
  return (
    <div className="rounded-xl border border-zinc-200 bg-white">
      <div className="flex items-center justify-between border-b border-zinc-100 px-5 py-3.5">
        <div className="h-4 w-36 animate-pulse rounded bg-zinc-100" />
      </div>
      <div className="divide-y divide-zinc-100">
        {[1, 2, 3].map((i) => (
          <div key={i} className="flex items-center gap-4 px-4 py-3">
            <div className="h-5 w-14 animate-pulse rounded-full bg-zinc-100" />
            <div className="flex-1 space-y-1.5">
              <div className="h-3.5 w-32 animate-pulse rounded bg-zinc-100" />
              <div className="h-3 w-48 animate-pulse rounded bg-zinc-100" />
            </div>
            <div className="h-5 w-16 animate-pulse rounded-full bg-zinc-100" />
          </div>
        ))}
      </div>
    </div>
  );
}
