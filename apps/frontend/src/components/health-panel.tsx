import { STATUS_COLORS } from "@/lib/constants";
import type { DatasetHealth } from "@/lib/api/types";

type Props = {
  health: DatasetHealth;
};

export const HealthPanel = ({ health }: Props) => {
  return (
    <div className="rounded-lg border border-zinc-200 bg-white">
      <div className="border-b border-zinc-100 px-4 py-3">
        <h3 className="text-sm font-semibold text-zinc-900">Dataset Health</h3>
      </div>
      <div className="grid grid-cols-2 gap-4 p-4">
        <Metric label="Row Count" value={health.row_count.toLocaleString()} />
        <Metric label="Column Count" value={health.column_count.toString()} />
        <Metric label="Warnings" value={health.warning_count.toString()} />
        <Metric
          label="Missing Mappings"
          value={health.missing_required_mappings ? "Yes" : "No"}
          valueClass={health.missing_required_mappings ? "text-red-600" : "text-green-600"}
        />
        <div>
          <span className="text-xs font-medium text-zinc-500">Last Run Status</span>
          <div className="mt-0.5">
            {health.last_run_status ? (
              <span
                className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${
                  STATUS_COLORS[health.last_run_status] || "bg-zinc-100 text-zinc-600"
                }`}
              >
                {health.last_run_status}
              </span>
            ) : (
              <span className="text-sm text-zinc-400">None</span>
            )}
          </div>
        </div>
        <Metric
          label="Last Published Version"
          value={health.last_published_version?.toString() ?? "None"}
        />
        <div className="col-span-2">
          <span className="text-xs font-medium text-zinc-500">Freshness</span>
          <p className="mt-0.5 text-sm text-zinc-700">
            {health.freshness_at
              ? new Date(health.freshness_at).toLocaleString()
              : "Unknown"}
          </p>
        </div>
      </div>
    </div>
  );
}

const Metric = ({
  label,
  value,
  valueClass,
}: {
  label: string;
  value: string;
  valueClass?: string;
}) => {
  return (
    <div>
      <span className="text-xs font-medium text-zinc-500">{label}</span>
      <p className={`mt-0.5 text-sm font-semibold ${valueClass || "text-zinc-900"}`}>
        {value}
      </p>
    </div>
  );
}
