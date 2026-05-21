import type { SummaryBrief } from "./dashboard-mappers";

type Props = {
  summary: SummaryBrief;
};

export const DashboardAiSummaryPanel = ({ summary }: Props) => {
  return (
    <div className="rounded-xl border border-zinc-200 bg-white p-5">
      <div className="flex items-center gap-2 mb-3">
        <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded bg-zinc-100 text-[10px] font-bold text-zinc-500">
          AI
        </span>
        <h3 className="text-xs font-semibold uppercase tracking-wider text-zinc-400">
          AI Summary
        </h3>
      </div>
      <p className="text-sm font-medium text-zinc-900">{summary.headline}</p>
      <ul className="mt-2 space-y-1">
        {summary.bullets.map((bullet, i) => (
          <li key={i} className="flex items-start gap-2 text-sm text-zinc-600">
            <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-zinc-300" />
            <span>{bullet}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export const DashboardAiSummaryPanelSkeleton = () => {
  return (
    <div className="rounded-xl border border-zinc-200 bg-white p-5">
      <div className="flex items-center gap-2 mb-3">
        <div className="h-5 w-5 animate-pulse rounded bg-zinc-100" />
        <div className="h-3 w-20 animate-pulse rounded bg-zinc-100" />
      </div>
      <div className="h-4 w-full animate-pulse rounded bg-zinc-100" />
      <div className="mt-2 space-y-1">
        <div className="h-3.5 w-3/4 animate-pulse rounded bg-zinc-100" />
        <div className="h-3.5 w-2/3 animate-pulse rounded bg-zinc-100" />
        <div className="h-3.5 w-1/2 animate-pulse rounded bg-zinc-100" />
      </div>
    </div>
  );
}
