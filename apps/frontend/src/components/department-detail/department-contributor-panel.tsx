import type { ContributorItem } from "./department-detail-mappers";
import { formatCurrency } from "@/lib/formatters";

type Props = {
  title: string;
  items: ContributorItem[];
};

export const DepartmentContributorPanel = ({ title, items }: Props) => {
  if (items.length === 0) {
    return (
      <div className="rounded-xl border border-zinc-200 bg-white p-5">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-zinc-400">
          {title}
        </h3>
        <p className="mt-4 text-sm text-zinc-400 text-center">No data available</p>
      </div>
    );
  }

  const maxTotal = items[0].total;

  return (
    <div className="rounded-xl border border-zinc-200 bg-white flex flex-col">
      <div className="border-b border-zinc-100 px-5 py-3.5">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-zinc-400">
          {title}
        </h3>
      </div>
      <div className="divide-y divide-zinc-100">
        {items.map((item) => (
          <div
            key={item.id}
            className="flex items-center gap-3 px-5 py-3"
          >
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium text-zinc-900">
                {item.name}
              </p>
              <div className="mt-1.5 h-1.5 w-full rounded-full bg-zinc-100">
                <div
                  className="h-1.5 rounded-full bg-zinc-800 transition-all"
                  style={{ width: `${maxTotal > 0 ? (item.total / maxTotal) * 100 : 0}%` }}
                />
              </div>
            </div>
            <span className="shrink-0 text-sm font-semibold tabular-nums text-zinc-900">
              {formatCurrency(item.total)}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

export const DepartmentContributorPanelSkeleton = () => {
  return (
    <div className="rounded-xl border border-zinc-200 bg-white">
      <div className="border-b border-zinc-100 px-5 py-3.5">
        <div className="h-3 w-28 animate-pulse rounded bg-zinc-100" />
      </div>
      <div className="divide-y divide-zinc-100">
        {[1, 2, 3].map((i) => (
          <div key={i} className="flex items-center gap-3 px-5 py-3">
            <div className="flex-1 space-y-2">
              <div className="h-3.5 w-28 animate-pulse rounded bg-zinc-100" />
              <div className="h-1.5 w-full animate-pulse rounded bg-zinc-100" />
            </div>
            <div className="h-3.5 w-16 animate-pulse rounded bg-zinc-100" />
          </div>
        ))}
      </div>
    </div>
  );
}
