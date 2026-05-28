"use client";

import { useEffect, useState } from "react";
import { STATUS_COLORS } from "@/lib/constants";
import type { DatasetHealth, DriftEvent } from "@/lib/api/types";
import { fetchDriftEvents, clearDriftBlock } from "@/lib/api/data-source";

type Props = {
  health: DatasetHealth;
  datasetId: string;
};

export const HealthPanel = ({ health, datasetId }: Props) => {
  const [showDrift, setShowDrift] = useState(false);
  const [driftEvents, setDriftEvents] = useState<DriftEvent[]>([]);
  const [loadingEvents, setLoadingEvents] = useState(false);
  const [clearing, setClearing] = useState(false);

  const drift = health.schema_drift;
  const isBlocked = drift?.is_blocked ?? false;
  const hasDrift = drift?.drift_detected ?? false;
  const isBreaking = drift?.last_drift_is_breaking ?? false;

  useEffect(() => {
    if (!showDrift || driftEvents.length > 0) return;

    const run = async () => {
      setLoadingEvents(true);
      try {
        const events = await fetchDriftEvents(datasetId);
        setDriftEvents(events);
      } finally {
        setLoadingEvents(false);
      }
    };
    run();
  }, [showDrift, driftEvents.length, datasetId]);

  const handleClearBlock = async () => {
    setClearing(true);
    try {
      await clearDriftBlock(datasetId);
      window.location.reload();
    } finally {
      setClearing(false);
    }
  };

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
        {hasDrift && (
          <div className="col-span-2">
            <span className="text-xs font-medium text-zinc-500">Schema Drift</span>
            <div className="mt-1 flex items-center gap-2">
              {isBlocked ? (
                <span className="inline-block rounded-full bg-red-100 px-2 py-0.5 text-xs font-medium text-red-700">
                  Blocked
                </span>
              ) : isBreaking ? (
                <span className="inline-block rounded-full bg-orange-100 px-2 py-0.5 text-xs font-medium text-orange-700">
                  Breaking
                </span>
              ) : (
                <span className="inline-block rounded-full bg-yellow-100 px-2 py-0.5 text-xs font-medium text-yellow-700">
                  Non-Breaking
                </span>
              )}
              {drift?.last_drift_at && (
                <span className="text-xs text-zinc-500">
                  {new Date(drift.last_drift_at).toLocaleString()}
                </span>
              )}
            </div>
            {isBlocked && (
              <button
                onClick={handleClearBlock}
                disabled={clearing}
                className="mt-2 rounded bg-zinc-100 px-3 py-1 text-xs font-medium text-zinc-700 hover:bg-zinc-200 disabled:opacity-50"
              >
                {clearing ? "Clearing..." : "Clear Block"}
              </button>
            )}
          </div>
        )}
        {hasDrift && (
          <div className="col-span-2">
            <button
              onClick={() => setShowDrift(!showDrift)}
              className="text-xs font-medium text-blue-600 hover:text-blue-800"
            >
              {showDrift ? "Hide drift details" : "View drift details"}
            </button>
            {showDrift && (
              <div className="mt-2 max-h-48 overflow-y-auto rounded border border-zinc-200 bg-zinc-50 p-2">
                {loadingEvents ? (
                  <p className="text-xs text-zinc-500">Loading...</p>
                ) : driftEvents.length === 0 ? (
                  <p className="text-xs text-zinc-500">No drift events recorded.</p>
                ) : (
                  <ul className="space-y-2">
                    {driftEvents.map((evt) => (
                      <li key={evt.id} className="border-b border-zinc-100 pb-2 last:border-0">
                        <div className="flex items-center gap-2">
                          <span
                            className={`inline-block rounded px-1.5 py-0.5 text-xs font-medium ${
                              evt.is_breaking
                                ? "bg-red-100 text-red-700"
                                : "bg-yellow-100 text-yellow-700"
                            }`}
                          >
                            {evt.is_breaking ? "Breaking" : "Non-breaking"}
                          </span>
                          <span className="text-xs text-zinc-500">
                            {new Date(evt.created_at).toLocaleString()}
                          </span>
                          <span className="text-xs text-zinc-400">via {evt.detected_by}</span>
                        </div>
                        {evt.delta && (
                          <div className="mt-1 text-xs text-zinc-600">
                            {evt.delta.added.length > 0 && (
                              <span className="mr-2 text-green-600">
                                +{evt.delta.added.length} added
                              </span>
                            )}
                            {evt.delta.removed.length > 0 && (
                              <span className="mr-2 text-red-600">
                                -{evt.delta.removed.length} removed
                              </span>
                            )}
                            {evt.delta.type_changed.length > 0 && (
                              <span className="mr-2 text-orange-600">
                                ~{evt.delta.type_changed.length} type changes
                              </span>
                            )}
                            {evt.delta.renamed.length > 0 && (
                              <span className="mr-2 text-blue-600">
                                ↻ {evt.delta.renamed.length} renamed
                              </span>
                            )}
                          </div>
                        )}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            )}
          </div>
        )}
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
