import Link from "next/link";
import { formatCurrency } from "@/lib/formatters";
import { buildDashboardToAnomaliesLink } from "@/lib/navigation/links";
import type { TimeRangeKey } from "@/lib/navigation/time-range";
import type { MetricCard } from "./dashboard-mappers";

type Props = {
  cards: {
    totalSpend: MetricCard;
    payrollSpend: MetricCard;
    claimsSpend: MetricCard;
    attentionCount: MetricCard;
  };
  timeRange: TimeRangeKey;
};

const MetricValue = ({ value }: { value: number }) => {
  return (
    <p className="text-2xl font-semibold tracking-tight tabular-nums text-zinc-900">
      {formatCurrency(value)}
    </p>
  );
}

const MetricSkeleton = () => {
  return <div className="h-8 w-28 animate-pulse rounded bg-zinc-100" />;
}

export const DashboardSummaryGrid = ({ cards, timeRange }: Props) => {
  const attentionLink = buildDashboardToAnomaliesLink(timeRange);

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <div className="rounded-xl border border-zinc-200 bg-white p-6">
        <h3 className="text-xs font-medium uppercase tracking-wider text-zinc-500">
          {cards.totalSpend.label}
        </h3>
        <div className="mt-3">
          <MetricValue value={cards.totalSpend.value} />
        </div>
      </div>
      <div className="rounded-xl border border-zinc-200 bg-white p-6">
        <h3 className="text-xs font-medium uppercase tracking-wider text-zinc-500">
          {cards.payrollSpend.label}
        </h3>
        <div className="mt-3">
          <MetricValue value={cards.payrollSpend.value} />
        </div>
      </div>
      <div className="rounded-xl border border-zinc-200 bg-white p-6">
        <h3 className="text-xs font-medium uppercase tracking-wider text-zinc-500">
          {cards.claimsSpend.label}
        </h3>
        <div className="mt-3">
          <MetricValue value={cards.claimsSpend.value} />
        </div>
      </div>
      <Link
        href={attentionLink}
        className="rounded-xl border border-zinc-200 bg-white p-6 transition-colors hover:border-zinc-300 hover:bg-zinc-50"
      >
        <h3 className="text-xs font-medium uppercase tracking-wider text-zinc-500">
          {cards.attentionCount.label}
        </h3>
        <div className="mt-3">
          <p className="text-2xl font-semibold tracking-tight tabular-nums text-zinc-900">
            {cards.attentionCount.value}
          </p>
        </div>
      </Link>
    </div>
  );
}

export const DashboardSummaryGridSkeleton = () => {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {[1, 2, 3, 4].map((i) => (
        <div key={i} className="rounded-xl border border-zinc-200 bg-white p-6">
          <div className="h-3 w-20 animate-pulse rounded bg-zinc-100" />
          <div className="mt-3">
            <MetricSkeleton />
          </div>
        </div>
      ))}
    </div>
  );
}
