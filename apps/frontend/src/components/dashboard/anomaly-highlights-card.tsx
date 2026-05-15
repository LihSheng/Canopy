import Link from "next/link";
import { SummaryCard } from "./summary-card";
import { getSeverityColor } from "@/lib/formatters";
import type { Anomaly } from "@/lib/api/types";

export function AnomalyHighlightsCard({
  anomalies,
  loading,
}: {
  anomalies: Anomaly[];
  loading?: boolean;
}) {
  if (loading) {
    return (
      <SummaryCard title="Anomalies">
        <div className="space-y-3">
          {[1, 2].map((i) => (
            <div key={i} className="h-5 w-full animate-pulse rounded bg-zinc-100" />
          ))}
        </div>
      </SummaryCard>
    );
  }

  if (anomalies.length === 0) {
    return (
      <SummaryCard title="Anomalies">
        <p className="text-sm text-zinc-400">No anomalies detected</p>
      </SummaryCard>
    );
  }

  return (
    <SummaryCard title="Anomalies">
      <ul className="space-y-2">
        {anomalies.slice(0, 3).map((a) => (
          <li key={a.id}>
            <Link
              href="/dashboard/anomalies"
              className="block rounded-lg border px-3 py-2 transition-colors hover:bg-zinc-50"
              style={{
                borderColor:
                  a.severity === "high"
                    ? "rgb(254 202 202)"
                    : a.severity === "medium"
                      ? "rgb(253 230 138)"
                      : "rgb(191 219 254)",
              }}
            >
              <div className="flex items-center justify-between gap-2">
                <span className="text-sm font-medium text-zinc-900">
                  {a.department_name}
                </span>
                <span
                  className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium border ${getSeverityColor(a.severity)}`}
                >
                  {a.severity}
                </span>
              </div>
              <p className="mt-1 text-xs text-zinc-500 line-clamp-1">
                {a.description}
              </p>
            </Link>
          </li>
        ))}
      </ul>
      {anomalies.length > 3 && (
        <Link
          href="/dashboard/anomalies"
          className="mt-3 block text-xs font-medium text-zinc-500 hover:text-zinc-900 transition-colors"
        >
          View all {anomalies.length} anomalies
        </Link>
      )}
    </SummaryCard>
  );
}
